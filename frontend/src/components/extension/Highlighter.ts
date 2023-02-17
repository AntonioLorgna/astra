

import { Extension } from '@tiptap/core'
import { Node as ProsemirrorNode } from 'prosemirror-model'
import { Plugin, PluginKey, TextSelection } from 'prosemirror-state'
import { Decoration, DecorationSet } from 'prosemirror-view'

import HighlighterPlugin, { Result } from './HighlighterPlugin'


function runAllHighlighterPlugins(doc: ProsemirrorNode, plugins: Array<typeof HighlighterPlugin>) {
    const results = plugins.map(RegisteredHighlighterPlugin => {
        return new RegisteredHighlighterPlugin(doc).scan().getResults()
    }).flat()

    const decorations = results.map(result =>{
            const attrs = result.attrs || {}
            return Decoration.inline(result.from, result.to, {
                class: 'bg-red-200',
                ...attrs
            })
        }
    )

    return DecorationSet.create(doc, decorations)
}

export interface HighlighterOptions {
    plugins: Array<typeof HighlighterPlugin>,
}

export const Highlighter = Extension.create<HighlighterOptions>({
    name: 'highlighter',

    addOptions() {
        return {
            plugins: [],
        }
    },

    addProseMirrorPlugins() {
        const { plugins } = this.options

        return [
            new Plugin({
                key: new PluginKey('Highlighter'),
                state: {
                    init(_, { doc }) {
                        return runAllHighlighterPlugins(doc, plugins)
                    },
                    apply(transaction, oldState) {
                        return transaction.docChanged
                            ? runAllHighlighterPlugins(transaction.doc, plugins)
                            : oldState
                    },
                },
                props: {
                    decorations(state) {
                        return this.getState(state)
                    },
                    // handleClick(view, _, event) {
                    //     return;
                    //     const target = (event.target as IconDivElement)

                    //     if (/lint-icon/.test(target.className) && target.issue) {
                    //         const { from, to } = target.issue

                    //         view.dispatch(
                    //             view.state.tr
                    //                 .setSelection(TextSelection.create(view.state.doc, from, to))
                    //                 .scrollIntoView(),
                    //         )

                    //         return true
                    //     }

                    //     return false
                    // },
                    // handleDoubleClick(view, _, event) {
                    //     return;
                    //     const target = (event.target as IconDivElement)

                    //     if (/lint-icon/.test((event.target as HTMLElement).className) && target.issue) {
                    //         const prob = target.issue

                    //         if (prob.fix) {
                    //             prob.fix(view, prob)
                    //             view.focus()
                    //             return true
                    //         }
                    //     }

                    //     return false
                    // },
                },
            }),
        ]
    },
})