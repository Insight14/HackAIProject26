export const regions = [
  { id: 'texas', name: 'Texas', risk: 'high', score: 78, abbreviation: 'ERCOT' },
  { id: 'california', name: 'California', risk: 'medium', score: 52, abbreviation: 'CAISO' },
  { id: 'pjm', name: 'PJM (Mid-Atlantic)', risk: 'low', score: 28, abbreviation: 'PJM' },
  { id: 'miso', name: 'MISO (Midwest)', risk: 'medium', score: 45, abbreviation: 'MISO' },
];

export const stressScoreHistory = [
  { time: '06:00', score: 32 },
  { time: '08:00', score: 38 },
  { time: '10:00', score: 45 },
  { time: '12:00', score: 52 },
  { time: '14:00', score: 61 },
  { time: '16:00', score: 71 },
  { time: '18:00', score: 78 },
];

export const riskFactors = [
  { factor: 'Severe weather overlap', contribution: 35, severity: 'high' },
  { factor: 'Load anomaly detected', contribution: 25, severity: 'high' },
  { factor: 'Generation drop', contribution: 20, severity: 'medium' },
  { factor: 'Transmission disturbance', contribution: 20, severity: 'high' },
];

export const incidents = [
  {
    id: 1,
    timestamp: '2026-03-07T14:32:00',
    text: 'Transmission line failure due to severe storm activity in North Texas',
    eventType: 'transmission failure',
    cause: 'storm',
    severity: 'high',
    region: 'North Texas',
  },
  {
    id: 2,
    timestamp: '2026-03-07T13:15:00',
    text: 'Substation overload reported in Dallas-Fort Worth area',
    eventType: 'substation overload',
    cause: 'demand spike',
    severity: 'medium',
    region: 'Dallas-Fort Worth',
  },
  {
    id: 3,
    timestamp: '2026-03-07T12:45:00',
    text: 'Wind farm generation drop due to grid curtailment',
    eventType: 'generation curtailment',
    cause: 'grid stability',
    severity: 'medium',
    region: 'West Texas',
  },
];

export const sectorAlerts = [
  {
    sector: 'Hospitals',
    region: 'North Texas',
    recommendation: 'Activate backup power systems. Prepare for potential brownouts.',
    priority: 'high',
  },
  {
    sector: 'Telecom',
    region: 'North Texas',
    recommendation: 'Prepare tower backup power. Monitor cell site battery levels.',
    priority: 'high',
  },
  {
    sector: 'Transportation',
    region: 'North Texas',
    recommendation: 'Prepare signal contingency. Alert traffic management centers.',
    priority: 'medium',
  },
  {
    sector: 'Emergency Services',
    region: 'North Texas',
    recommendation: 'Ensure generator fuel levels. Activate emergency protocols.',
    priority: 'high',
  },
];
