import { Node as ProsemirrorNode } from 'prosemirror-model'
import { DecorationAttrs } from 'prosemirror-view';

type DataType = Record<string, any>;

export interface Result {
    data: DataType,
    attrs?: DecorationAttrs,
    from: number,
    to: number
}

export default class HighlighterPlugin {
    protected doc

    private results: Array<Result> = []

    constructor(doc: ProsemirrorNode) {
        this.doc = doc
    }

    record(newResult: Result) {
        this.results.push(newResult)
    }

    recordMany(newResults: Array<Result>) {
        this.results = this.results.concat(newResults);
    }

    scan() {
        return this
    }

    getResults() {
        return this.results
    }
}
