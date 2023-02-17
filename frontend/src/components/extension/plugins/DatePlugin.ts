import HighlighterPlugin, { Result } from '../HighlighterPlugin'

export enum AnchorType {
    start = 0,
    end = 1
}

interface Anchor {
    index: number,
    [0]: string,
    anchorType: AnchorType
}

interface AnchorRegExpExecArray extends RegExpExecArray, Anchor {}

export interface DateSelection {
    startAnchor: Anchor | null,
    endAnchor: Anchor | null,
    datetime: string | null,
}
export function emptyDateSelection() {
    return {
        startAnchor: null,
        endAnchor: null,
        datetime: null
    } as DateSelection
}

export class DatePlugin extends HighlighterPlugin {

    public palette = [
        'red-100',
        'orange-100',
        'lime-100',
        'green-100',
        'blue-100',
        'purple-100',
    ]
    private currentDateSelectionIndex = 0;

    // public regex = /D1[\w\W]+?(D0)/ig
    public regexStart = /D[1-9]/ig
    public regexEnd = /D0/ig

    private dateAnchorToResult(da: Anchor) {
        const result: Result = {
            from: da.index,
            to: da.index + da[0].length,
            attrs: {
                class: 'bg-gray-400',
                'data-datetime': da.anchorType === AnchorType.start ? da[0] : undefined,
            },
            data: {
                type: 'date',
                anchorType: da.anchorType,
                datetime: da.anchorType === AnchorType.start ? da[0] : undefined,
            },
        }
        return result;
    }

    private dateSelectionToResult(ds: DateSelection) {
        if (ds.datetime === null ||
            ds.startAnchor === null ||
            ds.endAnchor === null) {
            console.warn("Selection is empty!")
            return null;
        }

        let decoratorClass = 'bg-'+ this.palette[this.currentDateSelectionIndex % this.palette.length];
        this.currentDateSelectionIndex ++;
        const result: Result = {
            from: ds.startAnchor.index + ds.startAnchor[0].length,
            to: ds.endAnchor.index,
            attrs: {
                class: decoratorClass,
                'data-datetime': ds.datetime,
            },
            data: {
                type: 'dateselection',
                datetime: ds.datetime,
            }
        }
        return result;
    }

    scan() {
        this.currentDateSelectionIndex = 0;
        let selection = emptyDateSelection();

        this.doc.descendants((node: any, position: number) => {
            if (!node.isText) {
                return
            }
            let match: AnchorRegExpExecArray | null;
            let allMatches: Array<AnchorRegExpExecArray> = [];
            while ((match = this.regexStart.exec(node.text) as AnchorRegExpExecArray) !== null) {
                match.anchorType = AnchorType.start
                match.index += position
                allMatches.push(match)
            }
            while ((match = this.regexEnd.exec(node.text) as AnchorRegExpExecArray) !== null) {
                match.anchorType = AnchorType.end
                match.index += position
                allMatches.push(match)
            }
            allMatches = allMatches.sort((a, b) => a.index - b.index);
            allMatches.forEach(anchor => {
                this.record(this.dateAnchorToResult(anchor));

                if (anchor.anchorType == AnchorType.start) {
                    if (selection.startAnchor !== null) {
                        selection = {
                            ...selection,
                            startAnchor: selection.startAnchor,
                            endAnchor: anchor
                        }
                        this.record(this.dateSelectionToResult(selection)!);
                        selection = {
                            startAnchor: anchor,
                            endAnchor: null,
                            datetime: anchor[0]
                        };

                    } else if (selection.startAnchor === null) {
                        selection = {
                            ...emptyDateSelection(),
                            startAnchor: anchor,
                            datetime: anchor[0]
                        };
                    }
                } else if (anchor.anchorType == AnchorType.end) {
                    if (selection.startAnchor !== null) {
                        if (selection.endAnchor === null) {
                            selection.endAnchor = anchor;
                            this.record(this.dateSelectionToResult(selection)!);
                            selection = emptyDateSelection();
                        } else {
                            console.warn("Selection not empty!")
                            selection = emptyDateSelection();
                        }
                    } else {
                        if (selection.endAnchor !== null) {
                            console.warn("Selection not empty!")
                            selection = emptyDateSelection();
                        }
                    }
                }
            })
        });

        if (selection.startAnchor !== null && selection.endAnchor === null) {
            selection.endAnchor = {
                index: Number.MAX_SAFE_INTEGER,
                [0]: '',
                anchorType: AnchorType.end
            } as Anchor
            this.record(this.dateSelectionToResult(selection)!);
        }
        // selection = emptyDateSelection();


        return this
    }
}
