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


def _strip_html_tags(text: str) -> str:
    """Remove HTML tags from text for plain-text contexts.

    Args:
        text: Text that may contain HTML tags.

    Returns:
        Text with HTML tags removed.
    """
    return re.sub(r"<[^>]+>", "", text)


def _to_html_content(text: str) -> str:
    """Convert text to safe HTML content for QTI 2.1.

    Args:
        text: The text content.

    Returns:
        Safe HTML/XML content wrapped in CDATA if needed.
    """
    # Check if text contains HTML tags
    if re.search(r"<[^>]+>", text):
        return f"<![CDATA[{text}]]>"
    else:
        return xml_escape(text)


class QTI21Exporter(QTIExporter):
    """Exporter for QTI 2.1 format.

    Generates IMS Content Package with QTI 2.1 assessment items compatible
    with Canvas New Quizzes, Moodle 4+, and modern LMS systems.
    """

    @property
    def version(self) -> QTIVersion:
        return QTIVersion.V2_1

    def generate_manifest(self) -> str:
        """Generate IMS manifest for QTI 2.1 package.

        Returns:
            The imsmanifest.xml content.
        """
        # Build resource entries for each item
        item_resources = []
        for quiz in self.collection.quizzes:
            item_id = quiz.identifier
            item_resources.append(
                f'<resource identifier="{item_id}" type="imsqti_item_xmlv2p1" '
                f'href="items/{item_id}.xml">\n'
                f'  <file href="items/{item_id}.xml"/>\n'
                f"</resource>"
            )

        resources_xml = "\n".join(item_resources)

        manifest = f"""<?xml version="1.0" encoding="UTF-8"?>
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
{resources_xml}
  </resources>
</manifest>
"""
        return manifest

    def generate_assessment(self) -> str:
        """Generate assessment XML for QTI 2.1.

        Returns:
            The assessment.xml content.
        """
        # Build assessment item references
        item_refs = []
        for quiz in self.collection.quizzes:
            item_refs.append(
                f'<assessmentItemRef identifier="{quiz.identifier}" '
                f'href="items/{quiz.identifier}.xml"/>'
            )

        items_xml = "\n".join(item_refs)

        # Escape title for XML
        title = xml_escape(self.collection.title)

        assessment = f"""<?xml version="1.0" encoding="UTF-8"?>
<assessmentTest xmlns="http://www.imsglobal.org/xsd/imsqti_v2p1"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:schemaLocation="http://www.imsglobal.org/xsd/imsqti_v2p1 http://www.imsglobal.org/xsd/imsqti_v2p1.xsd"
               identifier="{self.collection.identifier}"
               title="{title}">
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
        return assessment

    def _generate_single_choice_item(self, quiz: Quiz) -> str:
        """Generate QTI 2.1 XML for a single-choice (choiceInteraction) question.

        Args:
            quiz: The Quiz object to convert.

        Returns:
            The assessmentItem XML content.
        """
        # Build simple choices
        choices = []
        for answer in quiz.answers:
            answer_content = _to_html_content(answer.text)
            choices.append(
                f'<simpleChoice identifier="{answer.identifier}">'
                f"{answer_content}</simpleChoice>"
            )

        choices_xml = "\n".join(choices)

        # Get correct answer
        correct_answer = quiz.correct_answers[0]

        # Build feedback if content exists
        feedback_xml = ""
        modal_feedback_xml = ""
        if quiz.content:
            content_html = _to_html_content(quiz.content)
            feedback_xml = '<outcomeDeclaration identifier="FEEDBACK" cardinality="single" baseType="identifier"/>\n'
            modal_feedback_xml = (
                f'<modalFeedback outcomeIdentifier="FEEDBACK" showHide="show" identifier="general">\n'
                f"  <div>{content_html}</div>\n"
                f"</modalFeedback>\n"
            )

        # Question content
        question_content = _to_html_content(quiz.question)
        title = xml_escape(_strip_html_tags(quiz.question)[:50])

        item = f"""<?xml version="1.0" encoding="UTF-8"?>
<assessmentItem xmlns="http://www.imsglobal.org/xsd/imsqti_v2p1"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:schemaLocation="http://www.imsglobal.org/xsd/imsqti_v2p1 http://www.imsglobal.org/xsd/imsqti_v2p1.xsd"
               identifier="{quiz.identifier}"
               title="{title}"
               adaptive="false"
               timeDependent="false">
  <responseDeclaration identifier="RESPONSE" cardinality="single" baseType="identifier">
    <correctResponse>
      <value>{correct_answer.identifier}</value>
    </correctResponse>
  </responseDeclaration>
  <outcomeDeclaration identifier="SCORE" cardinality="single" baseType="float">
    <defaultValue>
      <value>0</value>
    </defaultValue>
  </outcomeDeclaration>
{feedback_xml}  <itemBody>
    <div class="question">
      {question_content}
    </div>
    <choiceInteraction responseIdentifier="RESPONSE" shuffle="false" maxChoices="1">
{choices_xml}
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
{modal_feedback_xml}</assessmentItem>
"""
        return item

    def _generate_multiple_choice_item(self, quiz: Quiz) -> str:
        """Generate QTI 2.1 XML for a multiple-choice (checkbox) question.

        Args:
            quiz: The Quiz object to convert.

        Returns:
            The assessmentItem XML content.
        """
        # Build simple choices
        choices = []
        for answer in quiz.answers:
            answer_content = _to_html_content(answer.text)
            choices.append(
                f'<simpleChoice identifier="{answer.identifier}">'
                f"{answer_content}</simpleChoice>"
            )

        choices_xml = "\n".join(choices)

        # Build correct response values
        correct_values = []
        for answer in quiz.correct_answers:
            correct_values.append(f"<value>{answer.identifier}</value>")
        correct_values_xml = "\n".join(correct_values)

        # Build feedback if content exists
        feedback_xml = ""
        modal_feedback_xml = ""
        if quiz.content:
            content_html = _to_html_content(quiz.content)
            feedback_xml = '<outcomeDeclaration identifier="FEEDBACK" cardinality="single" baseType="identifier"/>\n'
            modal_feedback_xml = (
                f'<modalFeedback outcomeIdentifier="FEEDBACK" showHide="show" identifier="general">\n'
                f"  <div>{content_html}</div>\n"
                f"</modalFeedback>\n"
            )

        # Question content
        question_content = _to_html_content(quiz.question)
        title = xml_escape(_strip_html_tags(quiz.question)[:50])

        # For multiple choice, use map response for partial credit scoring
        item = f"""<?xml version="1.0" encoding="UTF-8"?>
<assessmentItem xmlns="http://www.imsglobal.org/xsd/imsqti_v2p1"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:schemaLocation="http://www.imsglobal.org/xsd/imsqti_v2p1 http://www.imsglobal.org/xsd/imsqti_v2p1.xsd"
               identifier="{quiz.identifier}"
               title="{title}"
               adaptive="false"
               timeDependent="false">
  <responseDeclaration identifier="RESPONSE" cardinality="multiple" baseType="identifier">
    <correctResponse>
{correct_values_xml}
    </correctResponse>
  </responseDeclaration>
  <outcomeDeclaration identifier="SCORE" cardinality="single" baseType="float">
    <defaultValue>
      <value>0</value>
    </defaultValue>
  </outcomeDeclaration>
{feedback_xml}  <itemBody>
    <div class="question">
      {question_content}
    </div>
    <choiceInteraction responseIdentifier="RESPONSE" shuffle="false" maxChoices="0">
{choices_xml}
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
{modal_feedback_xml}</assessmentItem>
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
