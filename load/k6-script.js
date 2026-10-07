import http from 'k6/http';
import { check, sleep } from 'k6';
export const options = {
  stages: [{ duration: '30s', target: 10 }, { duration: '2m', target: 100 }, { duration: '2m', target: 200 }, { duration: '1m', target: 0 }],
  thresholds: { http_req_failed: ['rate==0'], http_req_duration: ['p(95)<1500'] },
};
export default function () {
  const base = __ENV.BASE_URL || 'http://localhost:8080';
  const response = http.get(`${base}/api/complaints?page=1&page_size=100`, { headers: { Host: __ENV.SMOKE_HOST || 'civicpulse.local' } });
  check(response, { 'returns 200': r => r.status === 200 });
  sleep(0.1);
}
