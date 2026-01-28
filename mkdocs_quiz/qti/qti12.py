"""QTI 1.2 format exporter.

QTI 1.2 is the most widely supported format for LMS imports, particularly
for Canvas Classic Quizzes, Blackboard, and older LMS systems.

Reference: IMS Question & Test Interoperability Specification v1.2.1
"""

from __future__ import annotations

import re
from xml.sax.saxutils import escape as xml_escape

from .base import QTIExporter, QTIVersion
from .models import Quiz
from .utils import make_title, to_html_content


class QTI12Exporter(QTIExporter):
    """Exporter for QTI 1.2 format.

    Generates IMS Content Package with QTI 1.2 assessment items compatible
    with Canvas Classic Quizzes and other LMS systems.
    """

    @property
    def version(self) -> QTIVersion:
        return QTIVersion.V1_2

    def generate_manifest(self) -> str:
        """Generate IMS manifest for QTI 1.2 package."""
        item_resources = "\n".join(
            f'<resource identifier="{q.identifier}" type="imsqti_item_xmlv1p2" '
            f'href="items/{q.identifier}.xml">\n'
            f'  <file href="items/{q.identifier}.xml"/>\n'
            f"</resource>"
            for q in self.collection.quizzes
        )

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{self.collection.identifier}"
          xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"
          xmlns:imsmd="http://www.imsglobal.org/xsd/imsmd_v1p2"
          xmlns:imsqti="http://www.imsglobal.org/xsd/ims_qtiasiv1p2">
  <metadata>
    <schema>IMS Content</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations/>
  <resources>
    <resource identifier="assessment" type="imsqti_assessment_xmlv1p2" href="assessment.xml">
      <file href="assessment.xml"/>
    </resource>
{item_resources}
  </resources>
</manifest>
"""

    def generate_assessment(self) -> str:
        """Generate assessment XML for QTI 1.2."""
        items_xml = "\n".join(
            f'<itemref linkrefid="{q.identifier}"/>' for q in self.collection.quizzes
        )

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2">
  <assessment ident="{self.collection.identifier}" title="{xml_escape(self.collection.title)}">
    <qtimetadata>
      <qtimetadatafield>
        <fieldlabel>qmd_assessmenttype</fieldlabel>
        <fieldentry>Assessment</fieldentry>
      </qtimetadatafield>
    </qtimetadata>
    <section ident="root_section">
      <selection_ordering>
        <selection/>
      </selection_ordering>
{items_xml}
    </section>
  </assessment>
</questestinterop>
"""

    def _build_response_labels(self, quiz: Quiz) -> str:
        """Build QTI 1.2 response labels for all answers."""
        return "\n".join(
            f'<response_label ident="{a.identifier}">\n'
            f"  <material>\n"
            f'    <mattext texttype="text/html">{to_html_content(a.text)}</mattext>\n'
            f"  </material>\n"
            f"</response_label>"
            for a in quiz.answers
        )

    def _build_feedback(self, quiz: Quiz) -> str:
        """Build feedback XML if quiz has content."""
        if not quiz.content:
            return ""
        return (
            f'<itemfeedback ident="general_fb">\n'
            f"  <material>\n"
            f'    <mattext texttype="text/html">{to_html_content(quiz.content)}</mattext>\n'
            f"  </material>\n"
            f"</itemfeedback>\n"
        )

    def _generate_single_choice_item(self, quiz: Quiz) -> str:
        """Generate QTI 1.2 XML for a single-choice question."""
        correct_id = quiz.correct_answers[0].identifier

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2">
  <item ident="{quiz.identifier}" title="{make_title(quiz.question)}">
    <itemmetadata>
      <qtimetadata>
        <qtimetadatafield>
          <fieldlabel>question_type</fieldlabel>
          <fieldentry>multiple_choice_question</fieldentry>
        </qtimetadatafield>
      </qtimetadata>
    </itemmetadata>
    <presentation>
      <material>
        <mattext texttype="text/html">{to_html_content(quiz.question)}</mattext>
      </material>
      <response_lid ident="response1" rcardinality="Single">
        <render_choice>
{self._build_response_labels(quiz)}
        </render_choice>
      </response_lid>
    </presentation>
    <resprocessing>
      <outcomes>
        <decvar maxvalue="100" minvalue="0" varname="SCORE" vartype="Decimal"/>
      </outcomes>
      <respcondition continue="No">
        <conditionvar>
          <varequal respident="response1">{correct_id}</varequal>
        </conditionvar>
        <setvar action="Set" varname="SCORE">100</setvar>
      </respcondition>
    </resprocessing>
{self._build_feedback(quiz)}  </item>
</questestinterop>
"""

    def _generate_multiple_choice_item(self, quiz: Quiz) -> str:
        """Generate QTI 1.2 XML for a multiple-choice question."""
        points_per_answer = 100.0 / len(quiz.correct_answers)

        # Build scoring conditions
        score_conditions = []
        for a in quiz.correct_answers:
            score_conditions.append(
                f'<respcondition continue="Yes">\n'
                f"  <conditionvar>\n"
                f'    <varequal respident="response1">{a.identifier}</varequal>\n'
                f"  </conditionvar>\n"
                f'  <setvar action="Add" varname="SCORE">{points_per_answer:.2f}</setvar>\n'
                f"</respcondition>"
            )
        for a in quiz.incorrect_answers:
            score_conditions.append(
                f'<respcondition continue="Yes">\n'
                f"  <conditionvar>\n"
                f'    <varequal respident="response1">{a.identifier}</varequal>\n'
                f"  </conditionvar>\n"
                f'  <setvar action="Add" varname="SCORE">-{points_per_answer:.2f}</setvar>\n'
                f"</respcondition>"
            )

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2">
  <item ident="{quiz.identifier}" title="{make_title(quiz.question)}">
    <itemmetadata>
      <qtimetadata>
        <qtimetadatafield>
          <fieldlabel>question_type</fieldlabel>
          <fieldentry>multiple_answers_question</fieldentry>
        </qtimetadatafield>
      </qtimetadata>
    </itemmetadata>
    <presentation>
      <material>
        <mattext texttype="text/html">{to_html_content(quiz.question)}</mattext>
      </material>
      <response_lid ident="response1" rcardinality="Multiple">
        <render_choice>
{self._build_response_labels(quiz)}
        </render_choice>
      </response_lid>
    </presentation>
    <resprocessing>
      <outcomes>
        <decvar maxvalue="100" minvalue="0" varname="SCORE" vartype="Decimal"/>
      </outcomes>
{chr(10).join(score_conditions)}
    </resprocessing>
{self._build_feedback(quiz)}  </item>
</questestinterop>
"""

    def _build_fill_in_blank_presentation(self, quiz: Quiz) -> str:
        """Build QTI 1.2 presentation with text entry interactions for fill-in-blank.

        Args:
            quiz: The fill-in-the-blank quiz.

        Returns:
            XML string for the presentation section.
        """
        # Replace {{BLANK_N}} placeholders with response_str elements
        # Split the question by the placeholder pattern
        question_text = quiz.question
        parts = re.split(r"\{\{BLANK_(\d+)\}\}", question_text)

        presentation_parts = []
        blank_idx = 0

        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Text part - escape for XML
                if part.strip():
                    presentation_parts.append(
                        f"      <material>\n"
                        f'        <mattext texttype="text/html">{to_html_content(part)}</mattext>\n'
                        f"      </material>"
                    )
            else:
                # Blank placeholder - create response_str
                blank = quiz.blanks[blank_idx]
                presentation_parts.append(
                    f'      <response_str ident="{blank.identifier}" rcardinality="Single">\n'
                    f"        <render_fib>\n"
                    f"          <response_label/>\n"
                    f"        </render_fib>\n"
                    f"      </response_str>"
                )
                blank_idx += 1

        return "\n".join(presentation_parts)

    def _generate_fill_in_blank_item(self, quiz: Quiz) -> str:
        """Generate QTI 1.2 XML for a fill-in-the-blank question.

        Uses response_str with render_fib (fill-in-blank) for text entry.
        """
        # Build scoring conditions for each blank
        points_per_blank = 100.0 / len(quiz.blanks)
        score_conditions = []

        for blank in quiz.blanks:
            score_conditions.append(
                f'      <respcondition continue="Yes">\n'
                f"        <conditionvar>\n"
                f'          <varequal respident="{blank.identifier}" case="No">'
                f"{xml_escape(blank.correct_answer)}</varequal>\n"
                f"        </conditionvar>\n"
                f'        <setvar action="Add" varname="SCORE">{points_per_blank:.2f}</setvar>\n'
                f"      </respcondition>"
            )

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2">
  <item ident="{quiz.identifier}" title="{make_title(quiz.question)}">
    <itemmetadata>
      <qtimetadata>
        <qtimetadatafield>
          <fieldlabel>question_type</fieldlabel>
          <fieldentry>fill_in_multiple_blanks_question</fieldentry>
        </qtimetadatafield>
      </qtimetadata>
    </itemmetadata>
    <presentation>
{self._build_fill_in_blank_presentation(quiz)}
    </presentation>
    <resprocessing>
      <outcomes>
        <decvar maxvalue="100" minvalue="0" varname="SCORE" vartype="Decimal"/>
      </outcomes>
{chr(10).join(score_conditions)}
    </resprocessing>
{self._build_feedback(quiz)}  </item>
</questestinterop>
"""

    def generate_items(self) -> dict[str, str]:
        """Generate individual item XML files."""
        items = {}
        for q in self.collection.quizzes:
            if q.is_fill_in_blank:
                xml = self._generate_fill_in_blank_item(q)
            elif q.is_multiple_choice:
                xml = self._generate_multiple_choice_item(q)
            else:
                xml = self._generate_single_choice_item(q)
            items[f"items/{q.identifier}.xml"] = xml
        return items
