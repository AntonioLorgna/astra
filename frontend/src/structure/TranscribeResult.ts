import { JSONContent } from '@tiptap/react'

export interface Segment {
    start: number
    end: number
    text: string
}
export interface TranscribeResult {
    segments: Segment[]
    datetime_base: string
}

export class TranscribeResultAdapter {
    private static toTimedelta(sec_num: number) {
        let hours: string | number = Math.floor(sec_num / 3600);
        let minutes: string | number = Math.floor((sec_num - (hours * 3600)) / 60);
        let seconds: string | number = Math.floor(sec_num) - (hours * 3600) - (minutes * 60);

        if (hours < 10) hours = "0" + hours; 
        if (minutes < 10) minutes = "0" + minutes; 
        if (seconds < 10) seconds = "0" + seconds; 

        return hours + ':' + minutes + ':' + seconds;
    }

    static html(tr: TranscribeResult) {
        const ttd = TranscribeResultAdapter.toTimedelta;
        let res = tr.segments.reduce((prev, cur) => {
            return prev + `<p data-timeline="${ttd(cur.start)}" data-start="${cur.start}" data-end="${cur.end}">${cur.text}</p>`
        }, '');
        if (tr.segments.length > 0) {
            const last_seg = tr.segments.at(-1)!;
            res += `<p data-timeline="${ttd(last_seg.end)}"></p>`
        }
        return res;
    }

    static json(tr: TranscribeResult) {
        if (tr.segments.length == 0) {
            return undefined;
        }

        const ttd = TranscribeResultAdapter.toTimedelta;
        let res: JSONContent = {
            type: "doc",
            content: tr.segments.map((seg, i) => {

                const p: JSONContent = {
                    type: "paragraph",
                    attrs: {
                        "data-timeline": ttd(seg.start),
                        "data-start": String(seg.start),
                        "data-end": String(seg.end),
                    }
                }
                if (seg.text) {
                    p.content = [
                        {
                            type: "text",
                            text: seg.text
                        }
                    ]
                }
                return p;
            })
        }

        if (tr.segments.length > 0) {
            const seg = tr.segments.at(-1)!;
            res.content!.push({
                type: "paragraph",
                attrs: {
                    "data-timeline": ttd(seg.end)
                }
            })
        }
        return res;
    }

    static jsonToTR(doc: JSONContent, datetime_base?: string) {
        if (!datetime_base) {
            datetime_base = new Date().toISOString();
        }

        const res: TranscribeResult = {
            datetime_base: datetime_base,
            segments: doc.content!
                .filter((p) =>
                    p.attrs &&
                    Number(p.attrs["data-start"]) > 0 &&
                    Number(p.attrs["data-end"]) > 0)
                .map((p) => ({
                    start: Number(p.attrs!["data-start"]),
                    end: Number(p.attrs!["data-end"]),
                    text: String(p.content?.at(-1)?.text || "")
                }))
        }
        return res;
    }

}
