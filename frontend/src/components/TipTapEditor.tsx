import { EditorContent, Extensions, useEditor } from '@tiptap/react'
import Document from '@tiptap/extension-document'
import Text from '@tiptap/extension-text'
import History from '@tiptap/extension-history'
import TimelineParagraph from './extension/TimelineParagraph'
import MenuBar from './MenuBar'
import { Highlighter } from './extension/Highlighter'
import { DatePlugin } from './extension/plugins/DatePlugin'


export default ({dateHighlight = true}) => {
  const extensions: Extensions = [
    Document,
    Text,
    History,
    TimelineParagraph,
    
  ]

  if (dateHighlight) {
    extensions.push(Highlighter.configure({
      plugins: [
        DatePlugin
      ]
    }))
  }

  const editor = useEditor({
    extensions,
    content: `<p data-timeline="0.00.00">Lorem iD1psum doloD1r sit ameD1t, clearly D1consectetur adipisciD1ng elit.</p>
    <p data-timeline="0.00.00">LorD1em ipsum D1dolor D1sit amet, conD1sectetur adipiD1scing elit.</p>
    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. </p>
    <p data-timeline="0.00.00">Lorem ipsum D0dolor sit amet, consectetur adipiscing elit.</p>
    `
  })

  return (
    <div>
      <MenuBar editor={editor!} />
      <EditorContent editor={editor} spellCheck={true} />
    </div>
  )
}
