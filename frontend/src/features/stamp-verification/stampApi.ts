import { endpoints } from '../../shared/endpoints'
import { http } from '../../shared/httpService'
import type { ReferenceStamp, StampVerification } from './types'

export const stampApi = {
  verify: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return http.postForm<StampVerification>(endpoints.stampsVerify, form)
  },
  references: () => http.get<ReferenceStamp[]>(endpoints.stampsReferences),
}
