import os
import uuid
from django.db import models
from django.utils import timezone


class QuestionGroup(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Baja'),
        ('medium', 'Media'),
        ('hard', 'Alta'),
    ]

    question_group = models.ForeignKey(
        QuestionGroup, 
        related_name='questions', 
        on_delete=models.CASCADE
    )
    question_text = models.TextField()
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='medium'
    )
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.question_group.name} - Q{self.order}: {self.question_text[:30]}"


def alternative_image_upload_path(instance, filename):
    ext = filename.split('.')[-1] if '.' in filename else 'jpg'
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('alternatives/', new_filename)


class Alternative(models.Model):
    question = models.ForeignKey(
        Question, 
        related_name='alternatives', 
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to=alternative_image_upload_path, blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Q{self.question.order} - Alt {self.order}: {self.title}"


class Player(models.Model):
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class GameSession(models.Model):
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=False, db_index=True)
    alternatives_status = models.BooleanField(default=True)
    gc_question_status = models.BooleanField(default=True)
    current_player_session = models.ForeignKey(
        'PlayerSession',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='active_in_game_sessions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({'Al aire' if self.is_active else 'Fuera de aire'})"


class PlayerSession(models.Model):
    TIME_CHOICES = [
        (60, '1 Minuto'),
        (180, '3 Minutos'),
        (300, '5 Minutos'),
    ]
    TIMER_STATUS_CHOICES = [
        ('stopped', 'Detenido'),
        ('running', 'En curso'),
        ('paused', 'Pausado'),
    ]

    game_session = models.ForeignKey(
        GameSession, 
        related_name='player_sessions', 
        on_delete=models.CASCADE
    )
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    question_group = models.ForeignKey(QuestionGroup, on_delete=models.PROTECT)
    alternative_text_visibility = models.BooleanField(default=False)
    time_limit_seconds = models.IntegerField(choices=TIME_CHOICES, default=180)
    accumulated_seconds = models.IntegerField(default=0)
    timer_status = models.CharField(
        max_length=20, 
        choices=TIMER_STATUS_CHOICES, 
        default='stopped'
    )
    last_timer_start = models.DateTimeField(null=True, blank=True)

    current_question_index = models.IntegerField(default=0)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['game_session', 'order']),
        ]

    def __str__(self):
        return f"{self.player.name} en {self.game_session.name}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_question_group_id = None
        if not is_new:
            try:
                old_instance = PlayerSession.objects.get(pk=self.pk)
                old_question_group_id = old_instance.question_group_id
            except PlayerSession.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        group_changed = old_question_group_id is not None and old_question_group_id != self.question_group_id

        if (is_new or group_changed) and self.question_group:
            if group_changed:
                self.answers.all().delete()

            existing_q_ids = set(self.answers.values_list('question_id', flat=True))
            questions = self.question_group.questions.all().order_by('order')
            questions_to_create = [
                PlayerQuestionAnswer(player_session=self, question=q)
                for q in questions
                if q.id not in existing_q_ids
            ]
            if questions_to_create:
                PlayerQuestionAnswer.objects.bulk_create(questions_to_create)

            first_q = questions.first()
            if first_q:
                self.current_question_index = first_q.order
            else:
                self.current_question_index = 0
            super().save(update_fields=['current_question_index'])

    @property
    def correct_count(self):
        return self.answers.filter(status='correct').count()

    @property
    def incorrect_count(self):
        return self.answers.filter(status='incorrect').count()

    @property
    def postponed_count(self):
        return self.answers.filter(status='postponed').count()

    @property
    def pending_count(self):
        return self.answers.filter(status='pending').count()

    def calculate_current_elapsed_time(self):
        return min(self.accumulated_seconds, self.time_limit_seconds)

    def get_next_question_answer(self, start_from_order=None):
        answers = self.answers.select_related('question').order_by('question__order')
        if not answers.exists():
            return None

        current_order = start_from_order if start_from_order is not None else self.current_question_index

        # 1. Buscar primera pregunta 'pending' después de la pregunta actual
        next_pending = answers.filter(status='pending', question__order__gt=current_order).first()
        if next_pending:
            return next_pending

        # 2. Buscar primera pregunta 'pending' desde el inicio
        next_pending_from_start = answers.filter(status='pending').first()
        if next_pending_from_start:
            return next_pending_from_start

        # 3. Si no hay pendientes, buscar primera pregunta 'postponed' después de la actual
        next_postponed = answers.filter(status='postponed', question__order__gt=current_order).first()
        if next_postponed:
            return next_postponed

        # 4. Si no hay más adelante, buscar primera 'postponed' desde el inicio
        next_postponed_from_start = answers.filter(status='postponed').first()
        if next_postponed_from_start:
            return next_postponed_from_start

        return None


class PlayerQuestionAnswer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('correct', 'Correcta'),
        ('incorrect', 'Incorrecta'),
        ('postponed', 'Postergada'),
    ]

    player_session = models.ForeignKey(
        PlayerSession, 
        related_name='answers', 
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_alternative = models.ForeignKey(
        Alternative, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['question__order']
        indexes = [
            models.Index(fields=['player_session', 'status']),
            models.Index(fields=['player_session', 'question']),
        ]
        unique_together = ['player_session', 'question']

    def __str__(self):
        return f"{self.player_session.player.name} - Q{self.question.order}: {self.status}"
