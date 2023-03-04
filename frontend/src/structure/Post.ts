import { TranscribeResult } from "./TranscribeResult"


export interface Post {
    id: string
    type: string
    status: string
    title: string
    content: TranscribeResult
    user_id: string
    task_id: string
  
    createdAt: Date
    updatedAt: Date
  }