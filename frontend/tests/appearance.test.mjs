import test from 'node:test'
import assert from 'node:assert/strict'
import { acceptsAppearance, channels } from '../src/appearance.js'
test('appearance messages are limited to the parent and exact origin', () => {
 const parent = {}; const data = { type:'cms:appearance',version:1,mode:'dark' }
 assert.equal(acceptsAppearance({source:parent,origin:'https://church.test',data},parent,'https://church.test'),true)
 assert.equal(acceptsAppearance({source:{},origin:'https://church.test',data},parent,'https://church.test'),false)
 assert.equal(acceptsAppearance({source:parent,origin:'https://other.test',data},parent,'https://church.test'),false)
 assert.equal(acceptsAppearance({source:parent,origin:'https://church.test',data:{...data,version:2}},parent,'https://church.test'),false)
})
test('only hex colors become CSS channels', () => {
 assert.equal(channels('#2E68DD'),'46 104 221')
 assert.equal(channels('url(https://other.test)'),null)
 assert.equal(channels('red;display:none'),null)
})
