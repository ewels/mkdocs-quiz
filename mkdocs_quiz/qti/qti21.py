"""QTI 2.1 format exporter.

QTI 2.1 is the modern IMS standard, supported by Canvas New Quizzes,
Moodle 4+, and other contemporary LMS systems.

Reference: IMS Question & Test Interoperability Specification v2.1
"""

from __future__ import annotations

import re
from xml.sax.saxutils import escape as xml_escape

from .base import QTIExporter, QTIVersion
from .models import Quiz
from .utils import make_title, to_html_content


class QTI21Exporter(QTIExporter):
    """Exporter for QTI 2.1 format.

    Generates IMS Content Package with QTI 2.1 assessment items compatible
    with Canvas New Quizzes, Moodle 4+, and modern LMS systems.
    """

    @property
    def version(self) -> QTIVersion:
        return QTIVersion.V2_1

    def generate_manifest(self) -> str:
        """Generate IMS manifest for QTI 2.1 package."""
        item_resources = "\n".join(
            f'<resource identifier="{q.identifier}" type="imsqti_item_xmlv2p1" '
            f'href="items/{q.identifier}.xml">\n'
            f'  <file href="items/{q.identifier}.xml"/>\n'
            f"</resource>"
            for q in self.collection.quizzes
        )

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{self.collection.identifier}"
          xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"
          xmlns:imsmd="http://ltsc.ieee.org/xsd/LOM"
          xmlns:imsqti="http://www.imsglobal.org/xsd/imsqti_v2p1">
  <metadata>
    <schema>IMS Content</schema>
    <schemaversion>1.2</schemaversion>
    <imsmd:lom>
      <imsmd:general>
        <imsmd:title>
          <imsmd:string>{xml_escape(self.collection.title)}</imsmd:string>
        </imsmd:title>
      </imsmd:general>
    </imsmd:lom>
  </metadata>
  <organizations/>
  <resources>
    <resource identifier="assessment" type="imsqti_test_xmlv2p1" href="assessment.xml">
      <file href="assessment.xml"/>
    </resource>
{item_resources}
  </resources>
</manifest>
"""

    def generate_assessment(self) -> str:
        """Generate assessment XML for QTI 2.1."""
        items_xml = "\n".join(
            f'<assessmentItemRef identifier="{q.identifier}" href="items/{q.identifier}.xml"/>'
            for q in self.collection.quizzes
        )

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<assessmentTest xmlns="http://www.imsglobal.org/xsd/imsqti_v2p1"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:schemaLocation="http://www.imsglobal.org/xsd/imsqti_v2p1 http://www.imsglobal.org/xsd/imsqti_v2p1.xsd"
               identifier="{self.collection.identifier}"
               title="{xml_escape(self.collection.title)}">
  <outcomeDeclaration identifier="SCORE" cardinality="single" baseType="float">
    <defaultValue>
      <value>0</value>
    </defaultValue>
  </outcomeDeclaration>
  <testPart identifier="testPart1" navigationMode="nonlinear" submissionMode="individual">
    <assessmentSection identifier="section1" title="Main Section" visible="true">
{items_xml}
    </assessmentSection>
  </testPart>
</assessmentTest>
"""

    def _build_choices(self, quiz: Quiz) -> str:
        """Build QTI 2.1 simple choices for all answers."""
        return "\n".join(
            f'<simpleChoice identifier="{a.identifier}">{to_html_content(a.text)}</simpleChoice>'
            for a in quiz.answers
        )

    def _build_feedback(self, quiz: Quiz) -> tuple[str, str]:
        """Build feedback declarations and modal feedback if quiz has content.

        Returns:
            Tuple of (outcome declaration, modal feedback XML).
        """
        if not quiz.content:
            return "", ""

        declaration = (
            '<outcomeDeclaration identifier="FEEDBACK" '
            'cardinality="single" baseType="identifier"/>\n'
        )
        modal = (
            f'<modalFeedback outcomeIdentifier="FEEDBACK" '
            f'showHide="show" identifier="general">\n'
            f"  <div>{to_html_content(quiz.content)}</div>\n"
            f"</modalFeedback>\n"
        )
        return declaration, modal

    def _generate_single_choice_item(self, quiz: Quiz) -> str:
        """Generate QTI 2.1 XML for a single-choice question."""
        correct_id = quiz.correct_answers[0].identifier
        feedback_decl, modal_feedback = self._build_feedback(quiz)

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<assessmentItem xmlns="http://www.imsglobal.org/xsd/imsqti_v2p1"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:schemaLocation="http://www.imsglobal.org/xsd/imsqti_v2p1 http://www.imsglobal.org/xsd/imsqti_v2p1.xsd"
               identifier="{quiz.identifier}"
               title="{make_title(quiz.question)}"
               adaptive="false"
               timeDependent="false">
  <responseDeclaration identifier="RESPONSE" cardinality="single" baseType="identifier">
    <correctResponse>
      <value>{correct_id}</value>
    </correctResponse>
  </responseDeclaration>
  <outcomeDeclaration identifier="SCORE" cardinality="single" baseType="float">
    <defaultValue>
      <value>0</value>
    </defaultValue>
  </outcomeDeclaration>
{feedback_decl}  <itemBody>
    <div class="question">
      {to_html_content(quiz.question)}
    </div>
    <choiceInteraction responseIdentifier="RESPONSE" shuffle="false" maxChoices="1">
{self._build_choices(quiz)}
    </choiceInteraction>
  </itemBody>
  <responseProcessing>
    <responseCondition>
      <responseIf>
        <match>
          <variable identifier="RESPONSE"/>
          <correct identifier="RESPONSE"/>
        </match>
        <setOutcomeValue identifier="SCORE">
          <baseValue baseType="float">1</baseValue>
        </setOutcomeValue>
      </responseIf>
    </responseCondition>
  </responseProcessing>
{modal_feedback}</assessmentItem>
"""

    def _generate_multiple_choice_item(self, quiz: Quiz) -> str:
        """Generate QTI 2.1 XML for a multiple-choice question."""
        correct_values = "\n".join(f"<value>{a.identifier}</value>" for a in quiz.correct_answers)
        feedback_decl, modal_feedback = self._build_feedback(quiz)

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<assessmentItem xmlns="http://www.imsglobal.org/xsd/imsqti_v2p1"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:schemaLocation="http://www.imsglobal.org/xsd/imsqti_v2p1 http://www.imsglobal.org/xsd/imsqti_v2p1.xsd"
               identifier="{quiz.identifier}"
               title="{make_title(quiz.question)}"
               adaptive="false"
               timeDependent="false">
  <responseDeclaration identifier="RESPONSE" cardinality="multiple" baseType="identifier">
    <correctResponse>
{correct_values}
    </correctResponse>
  </responseDeclaration>
  <outcomeDeclaration identifier="SCORE" cardinality="single" baseType="float">
    <defaultValue>
      <value>0</value>
    </defaultValue>
  </outcomeDeclaration>
{feedback_decl}  <itemBody>
    <div class="question">
      {to_html_content(quiz.question)}
    </div>
    <choiceInteraction responseIdentifier="RESPONSE" shuffle="false" maxChoices="0">
{self._build_choices(quiz)}
    </choiceInteraction>
  </itemBody>
  <responseProcessing>
    <responseCondition>
      <responseIf>
        <match>
          <variable identifier="RESPONSE"/>
          <correct identifier="RESPONSE"/>
        </match>
        <setOutcomeValue identifier="SCORE">
          <baseValue baseType="float">1</baseValue>
        </setOutcomeValue>
      </responseIf>
    </responseCondition>
  </responseProcessing>
{modal_feedback}</assessmentItem>
"""

    def _build_fill_in_blank_response_declarations(self, quiz: Quiz) -> str:
        """Build response declarations for fill-in-the-blank quiz.

        Args:
            quiz: The fill-in-the-blank quiz.

        Returns:
            XML string for all response declarations.
        """
        declarations = []
        for blank in quiz.blanks:
            declarations.append(
                f'  <responseDeclaration identifier="{blank.identifier}" '
                f'cardinality="single" baseType="string">\n'
                f"    <correctResponse>\n"
                f"      <value>{xml_escape(blank.correct_answer)}</value>\n"
                f"    </correctResponse>\n"
                f"  </responseDeclaration>"
            )
        return "\n".join(declarations)

    def _build_fill_in_blank_body(self, quiz: Quiz) -> str:
        """Build the item body with inline text entry interactions.

        Args:
            quiz: The fill-in-the-blank quiz.

        Returns:
            XML string for the item body content.
        """
        # Replace {{BLANK_N}} placeholders with textEntryInteraction elements
        question_text = quiz.question
        parts = re.split(r"\{\{BLANK_(\d+)\}\}", question_text)

        body_parts = []
        blank_idx = 0

        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Text part
                if part.strip():
                    body_parts.append(to_html_content(part))
            else:
                # Blank placeholder - create textEntryInteraction
                blank = quiz.blanks[blank_idx]
                body_parts.append(
                    f'<textEntryInteraction responseIdentifier="{blank.identifier}" '
                    f'expectedLength="{max(10, len(blank.correct_answer) + 5)}"/>'
                )
                blank_idx += 1

        return " ".join(body_parts)

    def _build_fill_in_blank_response_processing(self, quiz: Quiz) -> str:
        """Build response processing for fill-in-the-blank quiz.

        Args:
            quiz: The fill-in-the-blank quiz.

        Returns:
            XML string for response processing.
        """
        # Each blank contributes equal points
        points_per_blank = 1.0 / len(quiz.blanks)

        conditions = []
        for blank in quiz.blanks:
            conditions.append(
                f"    <responseCondition>\n"
                f"      <responseIf>\n"
                f'        <stringMatch caseSensitive="false">\n'
                f'          <variable identifier="{blank.identifier}"/>\n'
                f'          <correct identifier="{blank.identifier}"/>\n'
                f"        </stringMatch>\n"
                f'        <setOutcomeValue identifier="SCORE">\n'
                f"          <sum>\n"
                f'            <variable identifier="SCORE"/>\n'
                f'            <baseValue baseType="float">{points_per_blank:.4f}</baseValue>\n'
                f"          </sum>\n"
                f"        </setOutcomeValue>\n"
                f"      </responseIf>\n"
                f"    </responseCondition>"
            )
        return "\n".join(conditions)

    def _generate_fill_in_blank_item(self, quiz: Quiz) -> str:
        """Generate QTI 2.1 XML for a fill-in-the-blank question.

        Uses textEntryInteraction for inline text entry.
        """
        feedback_decl, modal_feedback = self._build_feedback(quiz)

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<assessmentItem xmlns="http://www.imsglobal.org/xsd/imsqti_v2p1"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:schemaLocation="http://www.imsglobal.org/xsd/imsqti_v2p1 http://www.imsglobal.org/xsd/imsqti_v2p1.xsd"
               identifier="{quiz.identifier}"
               title="{make_title(quiz.question)}"
               adaptive="false"
               timeDependent="false">
{self._build_fill_in_blank_response_declarations(quiz)}
  <outcomeDeclaration identifier="SCORE" cardinality="single" baseType="float">
    <defaultValue>
      <value>0</value>
    </defaultValue>
  </outcomeDeclaration>
{feedback_decl}  <itemBody>
    <div class="question">
      {self._build_fill_in_blank_body(quiz)}
    </div>
  </itemBody>
  <responseProcessing>
{self._build_fill_in_blank_response_processing(quiz)}
  </responseProcessing>
{modal_feedback}</assessmentItem>
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
