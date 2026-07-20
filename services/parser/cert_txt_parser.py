"""
services/parser/cert_txt_parser.py
Спец-парсер сертификационного теста (в отличие от обычного парсера бота):
принимает только текстовую часть — задания Y1 (один правильный ответ из 4).
Использует тот же формат +/=/#, что и основной бот, чтобы админу не нужно
было учить новый синтаксис. Если в тексте задания или варианта ответа
встречается маркер рисунка — [рис], [rasm], [img], [сурат] (любой регистр) —
задание помечается needs_image=True: рисунок потом добавляется в интерфейсе
mini app (раздел «Редактировать» → загрузить изображение).
"""
import re

from dto.cert_dto import CertOptionDTO, CertQuestionDraftDTO
from services.parser.base import (
    ANSWER_SEP,
    ANSWER_SEP_INLINE,
    CORRECT_MARK,
    QUESTION_SEP,
    QUESTION_SEP_INLINE,
)

_IMAGE_MARKER = re.compile(r"\[(рис\.?|rasm|img|image|сурат)[^\]]*\]", re.IGNORECASE)


def _strip_marker(text: str) -> str:
    return _IMAGE_MARKER.sub("", text).strip()


def _has_marker(text: str) -> bool:
    return bool(_IMAGE_MARKER.search(text))


def _split(text: str, q_sep: re.Pattern, a_sep: re.Pattern) -> list[CertQuestionDraftDTO]:
    drafts: list[CertQuestionDraftDTO] = []
    for block in q_sep.split(text):
        block = block.strip()
        if not block:
            continue

        parts = [p.strip() for p in a_sep.split(block) if p.strip()]
        if len(parts) < 3:
            continue

        needs_image = _has_marker(parts[0])
        question_text = _strip_marker(parts[0])

        options: list[CertOptionDTO] = []
        for raw in parts[1:]:
            is_correct = raw.startswith(CORRECT_MARK)
            raw = raw.lstrip(CORRECT_MARK).strip()
            if _has_marker(raw):
                needs_image = True
            option_text = _strip_marker(raw)
            if option_text:
                options.append(CertOptionDTO(text=option_text, is_correct=is_correct))

        if question_text and options:
            drafts.append(CertQuestionDraftDTO(text=question_text, options=options, needs_image=needs_image))

    return drafts


def parse_cert_y1_text(text: str) -> list[CertQuestionDraftDTO]:
    """
    Разбирает текст сертификационного теста на задания типа Y1.
    Бросает ValueError, если ни одного задания не распознано.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    drafts = _split(text, QUESTION_SEP, ANSWER_SEP)
    if not drafts:
        drafts = _split(text, QUESTION_SEP_INLINE, ANSWER_SEP_INLINE)

    if not drafts:
        raise ValueError(
            "Не удалось найти ни одного задания. Формат: задания разделяются знаком +, "
            "варианты ответа — знаком =, правильный вариант начинается с #. "
            "Рисунок в задании отмечайте маркером [рис] — такое задание попадёт "
            "в раздел «Нужен рисунок» для доредактирования."
        )

    return drafts
