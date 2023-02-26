import { MainButton, useShowPopup, useThemeParams } from '@vkruglikov/react-telegram-web-app';
import ky from 'ky';
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom';
import TimelineParagraph from '../components/extension/TimelineParagraph';
import TipTapEditor from '../components/TipTapEditor';
import { Extensions, useEditor } from '@tiptap/react'
import Document from '@tiptap/extension-document'
import Text from '@tiptap/extension-text'
import History from '@tiptap/extension-history'
import { Highlighter } from '../components/extension/Highlighter';
import { DatePlugin } from '../components/extension/plugins/DatePlugin';

interface Post {
  id: string
  type: string
  status: string
  title: string
  content: string
  user_id: string
  task_id: string

  createdAt: Date
  updatedAt: Date
}

const Root = () => {
  const [colorScheme, themeParams] = useThemeParams();
  const showPopup = useShowPopup();
  const [searchParams, setSearchParams] = useSearchParams();
  const post_id = searchParams.get("post_id")
  const [post, setPost] = useState<Post>();

  const extensions: Extensions = [
    Document,
    Text,
    History,
    TimelineParagraph,

  ]
  const dateHighlight = false;
  if (dateHighlight) {
    extensions.push(Highlighter.configure({
      plugins: [
        DatePlugin
      ]
    }))
  }

  const editor = useEditor({
    extensions,
    content: "Загрузка...",
    onUpdate: ({ editor }) => {
      
    },
  })

  useEffect(() => {
    ky.get(`/api/post/${post_id}`).json<Post>()
      .then(function (post) {
        setPost(post);
      })
      .catch(function (error) {
        console.log(error.response?.data?.detail || error.response);
      })
  }, [post_id]);

  useEffect(() => {
    if (editor && post?.content) {
      editor.commands.setContent(post.content);
    }
  }, [post?.content]);

  const savePost = () => {
    ky.post(`/api/post/${post_id}`, {json: {content: editor?.getHTML()}}).json<Post>()
      .then(function (post) {
        setPost(post);
        showPopup({message: "Сохранено"});
      })
      .catch(function (error) {
        console.log(error.response?.data?.detail || error.response );
      })
  }





  return (
    <>
      <TipTapEditor editor={editor!} />
      <MainButton
        text="Сохранить"
        onClick={savePost}
      />
    </>
  )
}

export default Root