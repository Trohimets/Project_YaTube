from django.contrib.auth import get_user_model
import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache
from django import forms
from ..models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            id=1,
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Noname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': 'test-slug'})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': 1})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': 'Noname'})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_uses_correct_template(self):
        response = self.authorized_author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'})
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def check_post(self, first_object):
        post_author_0 = first_object.author.username
        post_text_0 = first_object.text
        post_id_0 = first_object.id
        post_image = first_object.image
        self.assertEqual(post_author_0, 'Author')
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_id_0, 1)
        self.assertEqual(post_image, 'posts/small.gif')

    def check_group(self, first_object):
        post_group_o = first_object.group.title
        self.assertEqual(post_group_o, 'Тестовая группа')

    def test_index_page_context(self):
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.check_post(first_object)
        self.check_group(first_object)
        check_title = response.context['title']
        check_text = response.context['text']
        self.assertEqual(check_title, 'Последние обновления на сайте')
        self.assertEqual(check_text, 'Это главная страница проекта Yatube')

    def test_index_cache(self):
        cache.clear()
        post = Post.objects.create(
            author=self.author,
            text='Тестовый кэша',
        )
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author = first_object.author.username
        post_text = first_object.text
        post_id = first_object.id
        self.assertEqual(post_author, 'Author')
        self.assertEqual(post_text, 'Тестовый кэша')
        self.assertEqual(post_id, 2)
        post.delete()
        self.assertIn(post_text, response.content.decode())

    def test_group_posts_correct_context(self):
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        first_object = response.context['page_obj'][0]
        self.check_post(first_object)
        self.check_group(first_object)
        group_check = response.context['group']
        self.assertEqual(group_check, self.group)

    def test_profile_correct_context(self):
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'Author'}))
        first_object = response.context['page_obj'][0]
        self.check_post(first_object)
        self.check_group(first_object)
        author_check = response.context['author']
        self.assertEqual(author_check, self.author)

    def test_post_detail_correct_context(self):
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1}))
        post_check = response.context['post']
        self.assertEqual(post_check, self.post)

    def test_post_create_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        response = self.authorized_author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_in_second_group(self):
        group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        Post.objects.create(
            author=self.author,
            text='Тестовый текст2',
            group=group2,
        )
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        first_object = response.context['page_obj'][0]
        post_id_0 = first_object.id
        self.assertEqual(post_id_0, 1)
        """ Т.к. последний пост в группе остался с id =1, значит пост,"""
        """ созданный в группе2, не попал в исходную группу. """


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Alisa')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(13):
            cls.post_i = Post.objects.create(
                author=cls.user,
                text='Тестовый текст',
                id=i,
                group=cls.group,
            )

    def test_index_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_first_page_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_second_page_contains_three_records(self):
        response = self.client.get(reverse((
            'posts:group_list'), kwargs={'slug': 'test-slug'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_profile_first_page_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': 'Alisa'})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_second_page_contains_three_records(self):
        response = self.client.get(reverse((
            'posts:profile'), kwargs={'username': 'Alisa'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            id=1,
        )
        cls.follower = User.objects.create_user(username='Follower')
        cls.user = User.objects.create_user(username='NotFollow')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.follower)

    def test_follower_see_posts(self):
        """Авторизованный пользователь может подписываться на авторов.
        Новая запись автора появляется в ленте тех,
        кто на него подписан"""
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'Author'}))
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author.username
        post_text_0 = first_object.text
        post_id_0 = first_object.id
        self.assertEqual(post_author_0, 'Author')
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_id_0, 1)

    def test_user_can_unfollow(self):
        """Авторизованный пользователь может отписываться от авторов"""
        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': 'Author'}))
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        count_posts = len(response.context['page_obj'])
        self.assertEqual(count_posts, 0)

    def test_user_not_see_unfollow_posts(self):
        """Новая запись пользователя не появляется
        в ленте тех, кто не подписан."""
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        response = self.authorized_user.get(
            reverse('posts:follow_index'))
        count_posts = len(response.context['page_obj'])
        self.assertEqual(count_posts, 0)
