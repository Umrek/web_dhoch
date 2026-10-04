import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, email: str, password: str | None, **extra: object) -> "User":
        if not email:
            raise ValueError("E-mail je povinný.")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra: object) -> "User":
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create(email, password, **extra)

    def create_superuser(self, email: str, password: str | None = None, **extra: object) -> "User":
        extra["is_staff"] = True
        extra["is_superuser"] = True
        if not password:
            raise ValueError("Superuživatel musí mít heslo.")
        return self._create(email, password, **extra)

    def get_by_natural_key(self, email: str) -> "User":
        return self.get(email__iexact=email)


class User(AbstractBaseUser, PermissionsMixin):
    """Account identity only. Musician data lives in ``musicians.MusicianProfile``.

    Roles are Django Groups (see ``accounts.roles``), not a string field.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("e-mail", max_length=254, unique=True)
    full_name = models.CharField("celé jméno", max_length=150)
    is_active = models.BooleanField(
        "aktivní", default=True, help_text="Neaktivní účet se nemůže přihlásit."
    )
    is_staff = models.BooleanField(
        "přístup do administrace",
        default=False,
        help_text="Nastavuje se automaticky podle rolí.",
    )
    date_joined = models.DateTimeField("vytvořeno", default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = "uživatel"
        verbose_name_plural = "uživatelé"
        ordering = ["full_name", "email"]
        permissions = [("access_portal", "Může používat portál pro členy kapely")]
        constraints = [
            models.UniqueConstraint(Lower("email"), name="accounts_user_email_ci_unique"),
        ]

    def save(self, *args: object, **kwargs: object) -> None:
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    def get_full_name(self) -> str:
        return self.full_name

    def get_short_name(self) -> str:
        return self.full_name.split(" ")[0] if self.full_name else self.email

    def __str__(self) -> str:
        return self.full_name or self.email
