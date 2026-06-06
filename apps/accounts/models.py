from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


# User를 생성하는 도우미 클래스 => email을 Id로 사용할 것이기 때문에 필요하다.
class UserManager(BaseUserManager):
    
    # 일반 사용자 생성 함수 => 회원가입 API에서 사용 예정
    def create_user(self, email, password=None, **extra_fields):
        # email을 로그인 ID로 사용할 것이기 때문에 필수 검사
        if not email:
            raise ValueError("이메일은 필수입니다.")

        email = self.normalize_email(email) 

        user = self.model(
            email=email,
            **extra_fields,
        )

        if password:
            user.set_password(password) # set_password()함수가 유저가 입력한 비밀번호를 해싱해서 저장.
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    nickname = models.CharField(max_length=30)
    agree_terms = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager() # User객체를 만들 때, UserManager 사용해라
    
    # 우리 프로젝트에서는 email이 ID라는 것을 알려주는 것. => 이거 없으면 Django는 기본적으로 `username`을 찾는다.
    USERNAME_FIELD = "email" 
    
    # DB 테이블 이름 직접 지정 => 이거 안쓰면 Django가 자동으로 accounts_user를 만든다    
    class Meta:
        db_table = "users"
        
    def __str__(self):
        return self.email


class Topic(models.Model):
    class TopicType(models.TextChoices):
        CATEGORY = "CATEGORY", "Category"
        SUBJECT = "SUBJECT", "Subject"
        SKILL = "SKILL", "Skill"

    parent_topic = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=150, unique=True)
    depth = models.IntegerField(default=0)
    topic_type = models.CharField(
        max_length=30,
        choices=TopicType.choices,
        default=TopicType.SKILL,
    )
    is_learning_unit = models.BooleanField(default=True)
    is_assessable = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "topics"

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    class PreferredLearningStyle(models.TextChoices):
        THEORY = "theory", "이론 중심"
        PRACTICE = "practice", "실습 중심"
        PROJECT = "project", "프로젝트 중심"
        VIDEO = "video", "영상 강의 중심"
        TEXT = "text", "문서/책 중심"
        BALANCED = "balanced", "균형형"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    available_weekly_hours = models.PositiveSmallIntegerField(default=0)
    preferred_learning_style = models.CharField(
        max_length=30,
        choices=PreferredLearningStyle.choices,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profiles"

    def __str__(self):
        return f"{self.user.email} profile"


class UserInterestTopic(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interest_topics",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="interested_users",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_interest_topics"
        unique_together = ("user", "topic")
