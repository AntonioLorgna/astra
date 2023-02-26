import { Editor, EditorContent } from '@tiptap/react'
import MenuBar from './MenuBar'
interface Props {
  editor: Editor
}
export default (props:Props) => {
  const {editor} = props
  return (
    <div>
      <MenuBar editor={editor} />
      <EditorContent editor={editor} spellCheck={true} />
    </div>
  )
}
