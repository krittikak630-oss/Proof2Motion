// Built-in result for samples/sample_evidence.txt. Lets the UI be shown with no API key / no internet.
export const DEMO = {
  title: 'Lakeview Lane water complaint',
  summary:
    'Residents of Lakeview Lane reported brown tap water for weeks and eleven households filed written complaints. An inspection found iron above the permitted limit in three of four samples, yet the ward office called the water safe. A corroded pipe was replaced, but no re-test results were shared.',
  claims: [
    {
      claim: 'Many households complained about discoloured water.',
      status: 'supported',
      support: [
        { file: 'sample_evidence.txt', quote: 'Eleven households have now filed written complaints with the ward office.', page: null, verified: true },
      ],
    },
    {
      claim: 'The water exceeded the permitted iron limit.',
      status: 'supported',
      support: [
        { file: 'sample_evidence.txt', quote: 'iron levels were above the permitted limit in three of the four samples', page: null, verified: true },
      ],
    },
    {
      claim: 'The water is safe to drink.',
      status: 'unsupported',
      note: 'The ward statement is quoted accurately, but the inspection report contradicts it.',
      support: [
        { file: 'sample_evidence.txt', quote: 'The ward office said the water is safe to drink', page: null, verified: true },
      ],
    },
    {
      claim: 'The problem was fixed by the pipe repair.',
      status: 'partial',
      support: [
        { file: 'sample_evidence.txt', quote: 'Contractors replaced a corroded 40-metre pipe section on Lakeview Lane.', page: null, verified: true },
      ],
    },
  ],
  gaps: [
    'No re-test results exist after the pipe was replaced on 20 March.',
    'The official statement of 15 March conflicts with the inspection report of 12 March.',
    'Residents still report a metallic smell and have received no new test results.',
  ],
  storyboard: [
    { scene: 1, title: 'The complaint', narration: 'In March, residents of Lakeview Lane noticed brown water coming from their taps, week after week.', visual: 'A tap running brown water over a white sink', on_screen_text: 'Three weeks of brown water', duration_sec: 5 },
    { scene: 2, title: 'Neighbours speak up', narration: 'Eleven households filed written complaints with the ward office.', visual: 'Eleven house icons lighting up one by one', on_screen_text: '11 households complain', duration_sec: 5 },
    { scene: 3, title: 'The test result', narration: 'A water board engineer sampled four taps. Three had iron above the permitted limit.', visual: 'Four sample vials, three turning red', on_screen_text: '3 of 4 samples fail', duration_sec: 6 },
    { scene: 4, title: 'The official answer', narration: 'The ward office said the water was safe. The inspection report says otherwise.', visual: 'A statement and a lab report side by side, marked in conflict', on_screen_text: 'Statement vs. test report', duration_sec: 6 },
    { scene: 5, title: 'What is still unknown', narration: 'A pipe was replaced, but no new test results have been shared. Residents are still waiting.', visual: 'A pipe section with a question mark over a test vial', on_screen_text: 'No re-test shared', duration_sec: 6 },
  ],
}

export const DEMO_VERIFICATION = { verified: 4, total: 4 }
