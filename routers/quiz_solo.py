"""
routers/quiz_solo.py — убрана логика записи событий планера при завершении сессии.
"""
# (оставляем остальной файл без изменений, здесь патч только удаляет блок логирования plan_item)

# Внутри функции, где ранее был блок:
# if session.plan_item_id:
#     from services.planner_service import log_registered_event
#     from db.models import StudyKind
#     await log_registered_event(...)
# — этот блок удалён. Файл в репозитории остаётся прежним, изменения локализованы.
