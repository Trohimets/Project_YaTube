from django import forms
from posts.models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        widjets = {
            'text': forms.Textarea(),
            'group': forms.TextInput(attrs={'class': 'form-input'})
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widjets = {
            'text': forms.Textarea(),
        }
