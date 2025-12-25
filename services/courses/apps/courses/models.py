from django.db import models
from django.utils.text import slugify


class Category(models.Model):

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Course(models.Model):

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    slug = models.SlugField(unique=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True, default=0
    )
    lessons_count = models.IntegerField(default=0)

    owner_mentor_id = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_lessons_count(self):
        total_lessons = 0
        for module in self.modules.all():
            total_lessons += module.lessons.count()

        if self.lessons_count != total_lessons:
            self.lessons_count = total_lessons
            Course.objects.filter(pk=self.pk).update(lessons_count=total_lessons)

    def __str__(self):
        return self.title


class CourseMentor(models.Model):

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="mentors")
    mentor_id = models.IntegerField()

    class Meta:
        unique_together = ("course", "mentor_id")

    def __str__(self):
        return f"Mentor {self.mentor_id} for course {self.course}"


class EnrollmentCache(models.Model):
    user_id = models.IntegerField()  # external Users Service
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )

    class Meta:
        unique_together = ("user_id", "course")

    def __str__(self):
        return f"User {self.user_id} -> Course {self.course_id}"
