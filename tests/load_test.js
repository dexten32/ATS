import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    stages: [
        { duration: '2m', target: 300 }, // ramp up to 300
        { duration: '6h', target: 300 }, // 6-hour soak test
        { duration: '2m', target: 0 },   // ramp down
    ],
    thresholds: {
        http_req_failed: ['rate<0.01'],
        http_req_duration: ['p(95)<1000'],
    },
};

export default function () {
    const BASE_URL = 'http://localhost:8000';

    const res = http.get(`${BASE_URL}/`);

    check(res, {
        'status is 200': (r) => r.status === 200,
        'content is valid': (r) => r.body.length > 0,
    });

    sleep(0.1);
}
