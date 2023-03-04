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
            'data-start': attributes['data-start'],
            'data-end': attributes['data-end'],
            class: `no-bg-white relative ml-[5rem]
            before:absolute before:left-[-5em] before:min-w-[5rem] before:min-h-[1.5rem] before:bg-slate-300 before:opacity-50 before:mr-2 before:px-1 before:content-[attr(data-timeline)]`
          }
        },
      },
      'data-start': {
        default: '0',
        renderHTML: attributes => {
          return {
            'data-start': attributes['data-start'],
          }
        },
      },
      'data-end': {
        default: '0',
        renderHTML: attributes => {
          return {
            'data-end': attributes['data-end'],
          }
        },
      }
    }
  }
})


export default TimelineParagraph