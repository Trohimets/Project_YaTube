from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Group, Post, Comment, Follow


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_model_Post_have_correct_object_names(self):
        post = PostModelTest.post
        expected_text = post.text[:15]
        self.assertEqual(str(post), expected_text)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_model_Group_have_correct_object_names(self):
        group = GroupModelTest.group
        expected_group = group.title
        self.assertEqual(str(group), expected_group)


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий тестового поста',
        )

    def test_model_Comment_have_correct_object_names(self):
        comment = CommentModelTest.comment
        expected_text = comment.text[:20]
        self.assertEqual(str(comment), expected_text)


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.author = User.objects.create_user(username='Author')
        cls.follow = Follow.objects.create(author=cls.author, user=cls.user)

    def test_model_Follow_have_correct_object_names(self):
        follow = FollowModelTest.follow
        expected_text = f'{self.user} подписан на {self.author}'
        self.assertEqual(str(follow), expected_text)
