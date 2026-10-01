# Importar aquí todos los modelos para que Alembic los detecte en autogenerate
from studyia.models.activity import Activity
from studyia.models.progress import Progress
from studyia.models.question import Question
from studyia.models.role import Role, RoleName
from studyia.models.topic import Topic
from studyia.models.user import User

__all__ = ["Activity", "Progress", "Question", "Role", "RoleName", "Topic", "User"]
