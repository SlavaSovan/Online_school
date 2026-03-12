from django.core.cache import cache


class CacheInvalidator:
    """Инвалидатор кэша"""

    @staticmethod
    def _delete_patterns(patterns):
        """Удаляет ключи по списку паттернов"""
        for pattern in patterns:
            cache.delete_pattern(pattern)

    @staticmethod
    def invalidate_course_cache(course_id=None, course_slug=None, category_id=None):
        """Инвалидирует кэш, связанный с курсами"""

        patterns = [
            "courses_list_*",
            "course_detail_*",
            "category_courses_*",
            "my_courses_*",
            "my_enrollments_*",
            "CourseListView:*",
            "CourseDetailPublicView:*",
            "CourseDetailPrivateView:*",
        ]

        if course_slug:
            patterns.extend(
                [
                    f"*{course_slug}*",
                    f"*course_slug_{course_slug}*",
                ]
            )

        if category_id:
            patterns.append(f"category_courses_{category_id}_*")

        CacheInvalidator._delete_patterns(patterns)

    @staticmethod
    def invalidate_category_cache(category_id=None, category_slug=None):
        """Инвалидирует кэш, связанный с категориями"""

        patterns = [
            "categories_list_*",
            "category_detail_*",
            "CategoryListView:*",
            "CategoryDetailView:*",
        ]

        if category_slug:
            patterns.append(f"*{category_slug}*")

        CacheInvalidator._delete_patterns(patterns)

    @staticmethod
    def invalidate_module_cache(course_slug=None, module_slug=None):
        """Инвалидирует кэш, связанный с модулями"""

        patterns = [
            "modules_list_*",
            "module_detail_*",
            "ModuleListView:*",
            "ModuleDetailView:*",
        ]

        if course_slug:
            patterns.append(f"*course_slug_{course_slug}*")

        if course_slug and module_slug:
            patterns.append(f"*{course_slug}_{module_slug}*")

        CacheInvalidator._delete_patterns(patterns)

    @staticmethod
    def invalidate_lesson_cache(course_slug=None, module_slug=None, lesson_slug=None):
        """Инвалидирует кэш, связанный с уроками"""

        patterns = [
            "lessons_list_*",
            "lesson_content_*",
            "lesson_detail_*",
            "LessonListView:*",
            "LessonContentListView:*",
            "LessonDetailView:*",
        ]

        if course_slug and module_slug:
            patterns.append(f"*{course_slug}_{module_slug}*")

        if course_slug and module_slug and lesson_slug:
            patterns.append(f"*{course_slug}_{module_slug}_{lesson_slug}*")

        CacheInvalidator._delete_patterns(patterns)
