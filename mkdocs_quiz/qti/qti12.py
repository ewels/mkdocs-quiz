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


def _strip_html_tags(text: str) -> str:
    """Remove HTML tags from text for plain-text contexts.

    Args:
        text: Text that may contain HTML tags.

    Returns:
        Text with HTML tags removed.
    """
    return re.sub(r"<[^>]+>", "", text)


def _to_html_content(text: str) -> str:
    """Convert text to safe HTML content for QTI.

    If text contains HTML, wraps in CDATA. Otherwise, escapes special characters.

    Args:
        text: The text content.

    Returns:
        Safe HTML/XML content.
    """
    # Check if text contains HTML tags
    if re.search(r"<[^>]+>", text):
        # Wrap HTML content in mattext with texttype="text/html"
        return f"<![CDATA[{text}]]>"
    else:
        # Plain text - escape XML special characters
        return xml_escape(text)


class QTI12Exporter(QTIExporter):
    """Exporter for QTI 1.2 format.

    Generates IMS Content Package with QTI 1.2 assessment items compatible
    with Canvas Classic Quizzes and other LMS systems.
    """

    @property
    def version(self) -> QTIVersion:
        return QTIVersion.V1_2

    def generate_manifest(self) -> str:
        """Generate IMS manifest for QTI 1.2 package.

        Returns:
            The imsmanifest.xml content.
        """
        # Build resource entries for each item
        item_resources = []
        for quiz in self.collection.quizzes:
            item_id = quiz.identifier
            item_resources.append(
                f'<resource identifier="{item_id}" type="imsqti_item_xmlv1p2" '
                f'href="items/{item_id}.xml">\n'
                f'  <file href="items/{item_id}.xml"/>\n'
                f"</resource>"
            )

        resources_xml = "\n".join(item_resources)

        manifest = f"""<?xml version="1.0" encoding="UTF-8"?>
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
{resources_xml}
  </resources>
</manifest>
"""
        return manifest

    def generate_assessment(self) -> str:
        """Generate assessment XML for QTI 1.2.

        Returns:
            The assessment.xml content.
        """
        # Build item references
        item_refs = []
        for quiz in self.collection.quizzes:
            item_refs.append(f'<itemref linkrefid="{quiz.identifier}"/>')

        items_xml = "\n".join(item_refs)

        # Escape title for XML
        title = xml_escape(self.collection.title)

        assessment = f"""<?xml version="1.0" encoding="UTF-8"?>
<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2">
  <assessment ident="{self.collection.identifier}" title="{title}">
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
        return assessment

    def _generate_single_choice_item(self, quiz: Quiz) -> str:
        """Generate QTI 1.2 XML for a single-choice (radio) question.

        Args:
            quiz: The Quiz object to convert.

        Returns:
            The item XML content.
        """
        # Build response labels (answer options)
        response_labels = []
        for answer in quiz.answers:
            answer_content = _to_html_content(answer.text)
            response_labels.append(
                f'<response_label ident="{answer.identifier}">\n'
                f"  <material>\n"
                f'    <mattext texttype="text/html">{answer_content}</mattext>\n'
                f"  </material>\n"
                f"</response_label>"
            )

        responses_xml = "\n".join(response_labels)

        # Get correct answer identifier
        correct_answer = quiz.correct_answers[0]

        # Build feedback if content exists
        feedback_xml = ""
        if quiz.content:
            content_html = _to_html_content(quiz.content)
            feedback_xml = (
                f'<itemfeedback ident="general_fb">\n'
                f"  <material>\n"
                f'    <mattext texttype="text/html">{content_html}</mattext>\n'
                f"  </material>\n"
                f"</itemfeedback>\n"
            )

        # Question content
        question_content = _to_html_content(quiz.question)
        title = xml_escape(_strip_html_tags(quiz.question)[:50])

        item = f"""<?xml version="1.0" encoding="UTF-8"?>
<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2">
  <item ident="{quiz.identifier}" title="{title}">
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
        <mattext texttype="text/html">{question_content}</mattext>
      </material>
      <response_lid ident="response1" rcardinality="Single">
        <render_choice>
{responses_xml}
        </render_choice>
      </response_lid>
    </presentation>
    <resprocessing>
      <outcomes>
        <decvar maxvalue="100" minvalue="0" varname="SCORE" vartype="Decimal"/>
      </outcomes>
      <respcondition continue="No">
        <conditionvar>
          <varequal respident="response1">{correct_answer.identifier}</varequal>
        </conditionvar>
        <setvar action="Set" varname="SCORE">100</setvar>
      </respcondition>
    </resprocessing>
{feedback_xml}  </item>
</questestinterop>
"""
        return item

    def _generate_multiple_choice_item(self, quiz: Quiz) -> str:
        """Generate QTI 1.2 XML for a multiple-choice (checkbox) question.

        Args:
            quiz: The Quiz object to convert.

        Returns:
            The item XML content.
        """
        # Build response labels (answer options)
        response_labels = []
        for answer in quiz.answers:
            answer_content = _to_html_content(answer.text)
            response_labels.append(
                f'<response_label ident="{answer.identifier}">\n'
                f"  <material>\n"
                f'    <mattext texttype="text/html">{answer_content}</mattext>\n'
                f"  </material>\n"
                f"</response_label>"
            )

        responses_xml = "\n".join(response_labels)

        # Build scoring conditions for multiple answers
        # Each correct answer selected adds points, each wrong answer selected subtracts
        correct_ids = [a.identifier for a in quiz.correct_answers]
        incorrect_ids = [a.identifier for a in quiz.incorrect_answers]

        # Points per correct answer
        points_per_answer = 100.0 / len(correct_ids) if correct_ids else 0

        score_conditions = []
        for answer_id in correct_ids:
            score_conditions.append(
                f'<respcondition continue="Yes">\n'
                f"  <conditionvar>\n"
                f'    <varequal respident="response1">{answer_id}</varequal>\n'
                f"  </conditionvar>\n"
                f'  <setvar action="Add" varname="SCORE">{points_per_answer:.2f}</setvar>\n'
                f"</respcondition>"
            )

        # Penalty for selecting wrong answers
        for answer_id in incorrect_ids:
            score_conditions.append(
                f'<respcondition continue="Yes">\n'
                f"  <conditionvar>\n"
                f'    <varequal respident="response1">{answer_id}</varequal>\n'
                f"  </conditionvar>\n"
                f'  <setvar action="Add" varname="SCORE">-{points_per_answer:.2f}</setvar>\n'
                f"</respcondition>"
            )

        scoring_xml = "\n".join(score_conditions)

        # Build feedback if content exists
        feedback_xml = ""
        if quiz.content:
            content_html = _to_html_content(quiz.content)
            feedback_xml = (
                f'<itemfeedback ident="general_fb">\n'
                f"  <material>\n"
                f'    <mattext texttype="text/html">{content_html}</mattext>\n'
                f"  </material>\n"
                f"</itemfeedback>\n"
            )

        # Question content
        question_content = _to_html_content(quiz.question)
        title = xml_escape(_strip_html_tags(quiz.question)[:50])

        item = f"""<?xml version="1.0" encoding="UTF-8"?>
<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2">
  <item ident="{quiz.identifier}" title="{title}">
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
        <mattext texttype="text/html">{question_content}</mattext>
      </material>
      <response_lid ident="response1" rcardinality="Multiple">
        <render_choice>
{responses_xml}
        </render_choice>
      </response_lid>
    </presentation>
    <resprocessing>
      <outcomes>
        <decvar maxvalue="100" minvalue="0" varname="SCORE" vartype="Decimal"/>
      </outcomes>
{scoring_xml}
    </resprocessing>
{feedback_xml}  </item>
</questestinterop>
"""
        return item

    def generate_items(self) -> dict[str, str]:
        """Generate individual item XML files.

        Returns:
            Dictionary mapping filenames to XML content.
        """
        items = {}

        for quiz in self.collection.quizzes:
            if quiz.is_multiple_choice:
                xml_content = self._generate_multiple_choice_item(quiz)
            else:
                xml_content = self._generate_single_choice_item(quiz)

            filename = f"items/{quiz.identifier}.xml"
            items[filename] = xml_content

        return items
