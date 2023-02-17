import Paragraph from '@tiptap/extension-paragraph'

const TimelineParagraph = Paragraph.extend({
  draggable: false,
  addAttributes() {
    return {
      'data-timeline': {
        default: '',

        renderHTML: attributes => {
          return {
            'data-timeline': attributes['data-timeline'],
            class: `bg-white relative ml-[4rem]
            before:absolute before:left-[-4em] before:min-w-[4rem] before:min-h-[1.5rem] before:bg-slate-300 before:opacity-50 before:mr-2 before:px-1 before:content-[attr(data-timeline)]`
          }
        },
      },
    }
  }
})


export default TimelineParagraph