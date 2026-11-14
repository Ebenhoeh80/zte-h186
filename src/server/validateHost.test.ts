import { describe, it, expect } from 'vitest';

import { validateModemHost } from './validateHost';

describe('validateModemHost', () => {
  describe('accepts private / local targets', () => {
    it.each([
      ['192.168.10.2', 'http://192.168.10.2'],
      ['10.0.0.1', 'http://10.0.0.1'],
      ['172.16.0.1', 'http://172.16.0.1'],
      ['172.31.255.254', 'http://172.31.255.254'],
      ['100.64.0.1', 'http://100.64.0.1'],
      ['192.168.10.2:8080', 'http://192.168.10.2:8080'],
      ['http://192.168.10.2', 'http://192.168.10.2'],
      ['https://192.168.10.2', 'https://192.168.10.2'],
    ])('%s -> %s', (input, baseUrl) => {
      const r = validateModemHost(input);
      expect(r.isValid).toBe(true);
      expect(r.baseUrl).toBe(baseUrl);
    });

    it('accepts an IPv6 ULA with brackets', () => {
      const r = validateModemHost('fd00::1');
      expect(r.isValid).toBe(true);
      expect(r.baseUrl).toBe('http://[fd00::1]');
    });

    it.each(['modem', 'router', 'zte.local', 'nas.lan', 'box.home'])(
      'accepts local name %s',
      (h) => {
        expect(validateModemHost(h).isValid).toBe(true);
      },
    );
  });

  describe('rejects dangerous targets (SSRF defense)', () => {
    it.each([
      '127.0.0.1',
      'localhost',
      '::1',
      '169.254.169.254',
      'metadata.google.internal',
      '8.8.8.8',
      '1.1.1.1',
      '93.184.216.34',
      'evil.com',
      'http://169.254.169.254',
      '169.254.1.1',
      '192.168.10.2.evil.com',
    ])('rejects %s', (h) => {
      expect(validateModemHost(h).isValid).toBe(false);
    });

    it('rejects an empty host', () => {
      expect(validateModemHost('').isValid).toBe(false);
    });

    it('rejects a non-http(s) scheme', () => {
      expect(validateModemHost('ftp://192.168.10.2').isValid).toBe(false);
    });

    it('rejects an out-of-range port', () => {
      expect(validateModemHost('192.168.10.2:99999').isValid).toBe(false);
    });
  });
});
