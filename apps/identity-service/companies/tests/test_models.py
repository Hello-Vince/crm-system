"""
Tests for Company model and hierarchy functionality.
"""
from django.test import TestCase

from companies.models import Company


class TestCompanyDescendantIds(TestCase):
    """Test company hierarchy and descendant retrieval."""

    def test_single_level_hierarchy(self):
        """Test basic parent-child relationship."""
        parent = Company.objects.create(name="Parent")
        child1 = Company.objects.create(name="Child 1", parent=parent)
        child2 = Company.objects.create(name="Child 2", parent=parent)

        descendant_ids = parent.get_descendant_ids()
        self.assertEqual(len(descendant_ids), 2)
        self.assertIn(child1.id, descendant_ids)
        self.assertIn(child2.id, descendant_ids)

    def test_multi_level_hierarchy(self):
        """Test multi-level hierarchy (grandchildren)."""
        parent = Company.objects.create(name="Parent")
        child = Company.objects.create(name="Child", parent=parent)
        grandchild = Company.objects.create(name="Grandchild", parent=child)

        descendant_ids = parent.get_descendant_ids()
        self.assertEqual(len(descendant_ids), 2)
        self.assertIn(child.id, descendant_ids)
        self.assertIn(grandchild.id, descendant_ids)

    def test_no_children_returns_empty_list(self):
        """Test company with no children."""
        parent = Company.objects.create(name="Parent")

        descendant_ids = parent.get_descendant_ids()
        self.assertEqual(descendant_ids, [])

    def test_complex_hierarchy(self):
        """Test complex hierarchy with multiple branches."""
        # Create a more complex hierarchy
        root = Company.objects.create(name="Root")
        branch1 = Company.objects.create(name="Branch 1", parent=root)
        branch2 = Company.objects.create(name="Branch 2", parent=root)

        # Branch 1 children
        branch1_child1 = Company.objects.create(name="B1 Child 1", parent=branch1)
        branch1_child2 = Company.objects.create(name="B1 Child 2", parent=branch1)

        # Branch 2 children
        branch2_child1 = Company.objects.create(name="B2 Child 1", parent=branch2)

        # Grandchildren
        grandchild = Company.objects.create(name="Grandchild", parent=branch1_child1)

        descendant_ids = root.get_descendant_ids()
        self.assertEqual(len(descendant_ids), 6)  # 5 children + 1 grandchild
        self.assertIn(branch1.id, descendant_ids)
        self.assertIn(branch2.id, descendant_ids)
        self.assertIn(branch1_child1.id, descendant_ids)
        self.assertIn(branch1_child2.id, descendant_ids)
        self.assertIn(branch2_child1.id, descendant_ids)
        self.assertIn(grandchild.id, descendant_ids)


class TestCompanyVisibilityScope(TestCase):
    """Test company visibility scope functionality."""

    def test_get_visibility_scope_includes_self_and_descendants(self):
        """Test that visibility scope includes company itself + descendants."""
        parent = Company.objects.create(name="Parent")
        child = Company.objects.create(name="Child", parent=parent)
        grandchild = Company.objects.create(name="Grandchild", parent=child)

        scope = parent.get_visibility_scope()
        self.assertEqual(len(scope), 3)
        self.assertIn(parent.id, scope)
        self.assertIn(child.id, scope)
        self.assertIn(grandchild.id, scope)

    def test_get_visibility_scope_single_company(self):
        """Test visibility scope for company with no children."""
        company = Company.objects.create(name="Single")

        scope = company.get_visibility_scope()
        self.assertEqual(len(scope), 1)
        self.assertEqual(scope[0], company.id)


class TestCompanyModel(TestCase):
    """Test Company model basic functionality."""

    def test_company_creation(self):
        """Test basic company creation."""
        company = Company.objects.create(name="Test Company")
        self.assertIsNotNone(company.id)
        self.assertEqual(company.name, "Test Company")
        self.assertIsNone(company.parent)

    def test_company_str_representation(self):
        """Test company string representation."""
        company = Company.objects.create(name="Test Company")
        self.assertEqual(str(company), "Test Company")

    def test_company_with_parent(self):
        """Test company with parent relationship."""
        parent = Company.objects.create(name="Parent")
        child = Company.objects.create(name="Child", parent=parent)

        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())
