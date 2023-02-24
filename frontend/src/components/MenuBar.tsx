import { Editor } from "@tiptap/react";

const MenuBar = ({ editor }: { editor: Editor }) => {
    if (!editor) {
        return null
    }
    const buttonClasses = "px-2 py-1 m-2 bg-blue-600 rounded";

    return (
        <>
            <button
                onClick={() => editor.chain().focus().unsetAllMarks().run()}
                className={buttonClasses}
            >
                clear marks
            </button>
            <button onClick={() => editor.chain().focus().clearNodes().run()}
                className={buttonClasses}
            >
                clear nodes
            </button>
            <button
                onClick={() => editor.chain().focus().setParagraph().run()}
                className={buttonClasses + (editor.isActive('paragraph') ? '' : 'opacity-50')}
            >
                paragraph
            </button>
            {/* <button
                onClick={() => editor.chain().focus().toggleCodeBlock().run()}
                className={buttonClasses + (editor.isActive('codeBlock') ? '' : 'opacity-50')}
            >
                code block
            </button>
            <button
                onClick={() => editor.chain().focus().toggleBlockquote().run()}
                className={buttonClasses + (editor.isActive('blockquote') ? '' : 'opacity-50')}
            >
                blockquote
            </button>
            <button onClick={() => editor.chain().focus().setHorizontalRule().run()}
                className={buttonClasses}
            >
                horizontal rule
            </button> */}
            <button
                onClick={() => editor.chain().focus().undo().run()}
                disabled={
                    !editor.can()
                        .chain()
                        .focus()
                        .undo()
                        .run()
                }
                className={buttonClasses}

            >
                undo
            </button>
            <button
                onClick={() => editor.chain().focus().redo().run()}
                disabled={
                    !editor.can()
                        .chain()
                        .focus()
                        .redo()
                        .run()
                }
                className={buttonClasses}

            >
                redo
            </button>
        </>
    )
}

export default MenuBar;