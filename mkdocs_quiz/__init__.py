"""MkDocs Quiz Plugin - Create interactive quizzes in your MkDocs documentation."""

from importlib.metadata import version

__version__ = version("mkdocs_quiz")

from mkdocs_quiz.plugin import MkDocsQuizPlugin

__all__ = ["MkDocsQuizPlugin"]
