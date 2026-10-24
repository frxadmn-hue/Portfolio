# -*- coding: utf-8 -*-
"""
CLI Demonstration Runner for Natura Siberica Secure Enterprise RAG Agent.
Demonstrates 100% On-Premise Vector Search (Qdrant) + Zero-Leakage Cryptographic Vault (152-FZ).
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from .models import DataClassification, DepartmentAccess, DocumentChunk
from .pii_sanitizer import EnterprisePrivacyGuard
from .vector_store import SecureQdrantStore


def seed_knowledge_base(store: SecureQdrantStore) -> None:
    docs = [
        DocumentChunk(
            chunk_id="DOC-RD-FORMULA-01",
            title="Регламент варки: Облепиховый комплекс масел для кончиков волос Professional",
            text=(
                "ТЕХНОЛОГИЧЕСКИЙ РЕГЛАМЕНТ ТР-2026-08 (КОММЕРЧЕСКАЯ ТАЙНА). "
                "Главный технолог-разработчик: Смирнова Елена Викторовна, "
                "паспорт РФ 4512 773190, СНИЛС 142-882-901 44, тел. +7 (916) 432-19-88. "
                "Рецептура: основа содержит ровно 22.5% масла алтайской облепихи холодного отжима, "
                "6.8% масла сибирского кедра и 1.5% чистоты экстракта лимонника нановекторного. "
                "Точная загрузка реактора: 125.0 кг на варку при температуре 42.5C. "
                "Оплата премиального сырья произведена с расчетного счета 40702810400000054321."
            ),
            department=DepartmentAccess.RD_LABORATORY,
            classification=DataClassification.COMMERCIAL_SECRET,
            author="Смирнова Е.В."
        ),
        DocumentChunk(
            chunk_id="DOC-LEG-CONTRACT-02",
            title="Условия поставки и протокол скидок для розничных сетей",
            text=(
                "Приложение № 4 к Договору поставки. Базовая скидка сети составляет 28% от прайс-листа. "
                "Ответственный юрист: Кузнецов Михаил (тел. 8-903-123-45-67). Отсрочка 30 дней."
            ),
            department=DepartmentAccess.LEGAL,
            classification=DataClassification.INTERNAL,
            author="Кузнецов М."
        ),
        DocumentChunk(
            chunk_id="DOC-PUB-BRAND-03",
            title="Миссия бренда Natura Siberica и органические фермы в Хакасии",
            text=(
                "Natura Siberica — первый в России органический косметический бренд, "
                "использующий силу дикорастущих трав Сибири и Дальнего Востока. Собственные сертифицированные "
                "эко-фермы расположены в Хакасии, на Сахалине и Камчатке."
            ),
            department=DepartmentAccess.ALL,
            classification=DataClassification.PUBLIC,
            author="PR Department"
        )
    ]

    for d in docs:
        store.index_document(d)


def run_privacy_guard_demo() -> None:
    store = SecureQdrantStore()
    vault = EnterprisePrivacyGuard()

    print("=" * 110)
    print("🛡️ NATURA SIBERICA | SECURE ENTERPRISE RAG & CRYPTOGRAPHIC PRIVACY VAULT")
    print("=" * 110)
    print("КОНТУР: 100% On-Premise Vector Database (Qdrant) | Стандарты: 152-ФЗ, 98-ФЗ (Коммерческая тайна)")
    print("-" * 110)

    # 1. Индексация документов
    seed_knowledge_base(store)
    print("✅ Успешно проиндексирована база знаний: R&D рецептуры, договоры, публичный брендбук.\n")

    # 2. Демонстрация RBAC изоляции
    query = "рецептура и точный процент масла алтайской облепихи"
    print(f"🔎 ПОИСКОВЫЙ ЗАПРОС: «{query}»")
    print("-" * 110)

    print("Попытка доступа №1: Сотрудник отдела Маркетинга (DepartmentAccess.ALL/MARKETING)...")
    results_marketing = store.search_with_rbac(query, user_dept=DepartmentAccess.ALL)
    print(f"  -> Найдено документов: {len(results_marketing)}")
    for r in results_marketing:
        print(f"     • [{r.classification}] {r.title} (Score: {r.score})")

    print("\nПопытка доступа №2: Ведущий химик-технолог R&D Лаборатории (DepartmentAccess.RD_LABORATORY)...")
    results_rd = store.search_with_rbac(query, user_dept=DepartmentAccess.RD_LABORATORY)
    print(f"  -> Доступ разрешен. Найдено документов: {len(results_rd)}")
    target_doc = results_rd[0]
    print(f"     • [{target_doc.classification}] {target_doc.title} (Score: {target_doc.score})")
    print("-" * 110)

    # 3. Санитизация и передача во внешние языковые модели (Zero-Leakage)
    print("[3] ПРЕДОТВРАЩЕНИЕ УТЕЧЕК ВО ВНЕШНИЕ ОБЛАЧНЫЕ ИИ (PRIVACY SANITIZATION):")
    print("Исходный текст документа из корпоративного контура:")
    print(f"«{target_doc.text_snippet[:220]}...»\n")

    sanitized_text, tokens, has_pii, has_formula = vault.sanitize_text(target_doc.text_snippet)
    print(f"🔒 ТЕКСТ ПОСЛЕ АНОНИМИЗАЦИИ В КРИПТО-ШЛЮЗЕ (Безопасно для отправки в любой внешний ИИ):")
    print("-" * 110)
    print(sanitized_text)
    print("-" * 110)
    print(f"📊 Статистика защиты: Вырезано и зашифровано сущностей: {len(tokens)}")
    print(f"   • Защита персональных данных (152-ФЗ): {'ОБНАРУЖЕНО И ЗАБЛОКИРОВАНО' if has_pii else 'НЕТ'}")
    print(f"   • Защита секретных рецептур и навесок (98-ФЗ): {'ОБНАРУЖЕНО И ЗАБЛОКИРОВАНО' if has_formula else 'НЕТ'}")
    print("-" * 110)

    # 4. Обратная де-анонимизация внутри безопасного контура
    restored_text = vault.restore_tokens(sanitized_text)
    print("🔓 ДЕ-АНОНИМИЗАЦИЯ ВНУТРИ ON-PREMISE СЕРВЕРА (Только для авторизованного сотрудника):")
    print(f"«{restored_text[:200]}...»")
    print("=" * 110)
    print("✅ Все данные локализованы на серверах в РФ. Утечка формул и ПДн технически исключена.")
    print("=" * 110)


if __name__ == "__main__":
    run_privacy_guard_demo()
