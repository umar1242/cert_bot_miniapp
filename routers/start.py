"""
routers/start.py — убрана логика регистрации планера и связанные deeplink'и.
"""
from keyboards.edit_kb import quiz_view_kb, myquiz_list_kb
from keyboards.settings_kb import language_kb, settings_kb
from keyboards.main_kb import main_reply_kb
from db.models import SessionMode

router = Router()


async def _show_main_menu(message: Message, user_id: int, db: AsyncSession, lang: str) -> None:
    """Главное меню — приветствие + список квизов. message используется только для .answer()."""
    quizzes = await get_user_quizzes(db, user_id)
    respondents = await get_respondents_batch(db, [q.id for q in quizzes])
    groups = group_quizzes(quizzes)
    text = t("start.welcome", lang) + fmt_quiz_list_grouped(groups, respondents, page=0, lang=lang)
    await message.answer(text, reply_markup=myquiz_list_kb(groups, page=0, lang=lang))


@router.message(CommandStart())
async def cmd_start(message: Message, db: AsyncSession, lang: str, bot) -> None:
    args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""

    # Нижняя эмодзи-навигация — ставим один раз при входе, дальше остаётся видна
    # под полем ввода независимо от инлайн-кнопок в последующих сообщениях.
    await message.answer("👋", reply_markup=main_reply_kb())

    quiz_id = parse_start_param(args)
    deck_id = parse_deck_start_param(args)

    # --- Deep link: открыть колоду ---
    if deck_id is not None:
        from services.flashcard_service import get_deck
        from keyboards.deck_kb import deck_view_kb, deck_shared_view_kb
        deck = await get_deck(db, deck_id)
        if deck is None:
            await message.answer(t("deck.not_found", lang))
            return
        is_owner = deck.owner_id == message.from_user.id
        kb = deck_view_kb(deck.id, lang) if is_owner else deck_shared_view_kb(deck.id, lang)
        await message.answer(
            t("deck.open_via_link", lang, title=deck.title, count=len(deck.cards)),
            reply_markup=kb,
        )
        return

    # --- Обычный /start без параметра ---
    if quiz_id is None:
        # Если пользователь ещё не выбирал язык — показываем выбор языка
        saved = await get_lang_raw(db, message.from_user.id)
        if saved is None:
            await message.answer(t("lang.choose", lang), reply_markup=language_kb("setlang"))
            return
        await _show_main_menu(message, message.from_user.id, db, lang)
        return

    # --- Deep link: запуск квиза ---
    quiz = await get_quiz(db, quiz_id)
    if quiz is None:
        await message.answer(t("common.quiz_not_found_deleted", lang))
        return

    existing = await get_active_session_by_chat(db, message.chat.id)
    if existing:
        await message.answer(t("start.chat_busy", lang))
        return

    if not await acquire_quiz_lock(quiz_id):
        await message.answer(t("start.quiz_launching", lang))
        return
    try:
        session = await create_solo_session(
            db, quiz_id, message.chat.id, message.from_user.id, message.from_user.username
        )
        await message.answer(t("start.quiz_started", lang, title=quiz.title), reply_markup=quiz_replay_kb(quiz.id, lang))
        await start_question_timer(
            session.id, session.quiz.questions[0].id, session.quiz.timer_sec,
            lambda sid, b: _next_question(sid, b), bot,
        )
    finally:
        await release_quiz_lock(quiz_id)
