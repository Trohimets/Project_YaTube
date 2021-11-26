from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from ..models import Group, Post, Comment, Follow


User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Author')
        cls.user = User.objects.create(username='Noname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            id=1
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='тестовый комментарий'
        )
        cls.follow = Follow.objects.create(
            author=cls.author,
            user=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(self.author)

    def test_static_pages(self):
        templates_code = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for adress, code in templates_code.items():
            with self.subTest(code=code):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, code)

    def test_guest_pages(self):
        templates_code = {
            '/': HTTPStatus.OK,
            '/group/test-slug/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
            '/profile/Noname/': HTTPStatus.OK,
            '/posts/1/edit/': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for adress, code in templates_code.items():
            with self.subTest(code=code):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, code)

    def test_post_create(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        response = self.authorized_author_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_redirect_anonimous(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_add_comment(self):
        response = self.authorized_client.get('/posts/1/comment')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_follow_index(self):
        response = self.authorized_client.get('/follow/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_follow(self):
        response = self.authorized_client.get('/profile/Author/follow/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unfollow(self):
        response = self.authorized_client.get('/profile/Author/unfollow/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            '/create/': 'posts/create_post.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/posts/1/': 'posts/post_detail.html',
            '/profile/Noname/': 'posts/profile.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_edit_uses_correct_template(self):
        """Страница по адресу / использует шаблон deals/home.html."""
        response = self.authorized_author_client.get('/posts/1/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
