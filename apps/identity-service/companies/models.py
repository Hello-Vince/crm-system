import uuid

from django.db import models


class Company(models.Model):
    """
    Company with self-referencing parent for hierarchy (A -> B, C).
    Parent company (A) can see all child company (B, C) records.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "companies"
        indexes = [
            models.Index(fields=['parent']),
        ]

    def __str__(self) -> str:
        return self.name

    def get_descendant_ids(self) -> list[uuid.UUID]:
        """Returns all child company IDs recursively (BFS)."""
        descendant_ids: list[uuid.UUID] = []
        queue = list(self.children.values_list('id', flat=True))
        while queue:
            child_id = queue.pop(0)
            descendant_ids.append(child_id)
            grandchildren = Company.objects.filter(
                parent_id=child_id
            ).values_list('id', flat=True)
            queue.extend(grandchildren)
        return descendant_ids

    def get_visibility_scope(self) -> list[uuid.UUID]:
        """Returns company ID + all descendant IDs for visibility filtering."""
        return [self.id] + self.get_descendant_ids()
