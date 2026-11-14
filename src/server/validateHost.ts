import net from 'net';

export interface HostValidation {
  isValid: boolean;
  baseUrl?: string;
  error?: string;
}

/**
 * Validates that the target modem host is within local/private network boundaries,
 * preventing Server-Side Request Forgery (SSRF) against cloud metadata, loopback, or external services.
 */
export function validateModemHost(hostInput: string): HostValidation {
  if (!hostInput || typeof hostInput !== 'string') {
    return { isValid: false, error: 'Host address is required.' };
  }

  const rawHost = hostInput.trim();
  let hostname = rawHost;
  let port: string | null = null;
  let protocol = 'http:';

  try {
    if (rawHost.includes('://')) {
      const parsed = new URL(rawHost);
      protocol = parsed.protocol;
      hostname = parsed.hostname;
      port = parsed.port;
    } else {
      if (rawHost.startsWith('[') && rawHost.includes(']')) {
        const endBracket = rawHost.indexOf(']');
        hostname = rawHost.substring(1, endBracket);
        const remainder = rawHost.substring(endBracket + 1);
        if (remainder.startsWith(':')) {
          port = remainder.substring(1);
        }
      } else if (rawHost.includes(':') && !rawHost.includes('.')) {
        hostname = rawHost;
      } else if (rawHost.includes(':')) {
        const parts = rawHost.split(':');
        hostname = parts[0];
        port = parts[1];
      }
    }
  } catch {
    return { isValid: false, error: 'Malformed host address or URL.' };
  }

  if (protocol !== 'http:' && protocol !== 'https:') {
    return { isValid: false, error: 'Only HTTP and HTTPS protocols are supported.' };
  }

  if (port) {
    const portNum = parseInt(port, 10);
    if (isNaN(portNum) || portNum < 1 || portNum > 65535) {
      return { isValid: false, error: 'Invalid port number.' };
    }
  }

  const cleanHostname = hostname.replace(/^\[|\]$/g, '').toLowerCase();

  const forbiddenHosts = ['metadata.google.internal', '169.254.169.254', 'localhost', '127.0.0.1', '::1'];
  if (forbiddenHosts.includes(cleanHostname)) {
    return { isValid: false, error: 'Access to loopback or cloud metadata services is forbidden.' };
  }

  const ipVersion = net.isIP(cleanHostname);

  if (ipVersion === 4) {
    const octets = cleanHostname.split('.').map(o => parseInt(o, 10));
    const [o0, o1] = octets;

    const is10 = o0 === 10;
    const is172Private = o0 === 172 && o1 >= 16 && o1 <= 31;
    const is192168 = o0 === 192 && o1 === 168;
    const isCgnat = o0 === 100 && o1 >= 64 && o1 <= 127;

    if (o0 === 169 && o1 === 254) {
      return { isValid: false, error: 'Link-local and cloud metadata addresses (169.254.x.x) are forbidden.' };
    }

    if (o0 === 127) {
      return { isValid: false, error: 'Loopback addresses (127.x.x.x) are forbidden.' };
    }

    if (!is10 && !is172Private && !is192168 && !isCgnat) {
      return { isValid: false, error: 'Target IPv4 address must be in a private RFC1918 range (e.g. 192.168.x.x, 10.x.x.x).' };
    }

    const portSuffix = port ? `:${port}` : '';
    return { isValid: true, baseUrl: `${protocol}//${cleanHostname}${portSuffix}` };
  } else if (ipVersion === 6) {
    if (cleanHostname === '::1') {
      return { isValid: false, error: 'IPv6 loopback (::1) is forbidden.' };
    }
    if (cleanHostname.startsWith('fe80:') || cleanHostname.startsWith('fc') || cleanHostname.startsWith('fd')) {
      const portSuffix = port ? `:${port}` : '';
      return { isValid: true, baseUrl: `${protocol}//[${cleanHostname}]${portSuffix}` };
    }
    return { isValid: false, error: 'Target IPv6 address must be a private ULA (fc00::/7) or link-local address.' };
  } else {
    if (!/^[a-zA-Z0-9.-]+$/.test(cleanHostname)) {
      return { isValid: false, error: 'Invalid hostname format.' };
    }
    const allowedSuffixes = ['.local', '.lan', '.home', '.home.arpa', '.localdomain'];
    const isAllowedSuffix = allowedSuffixes.some(suffix => cleanHostname.endsWith(suffix));
    const isSimpleLocalName = ['modem', 'router', 'zte-modem', 'zte'].includes(cleanHostname);

    if (!isAllowedSuffix && !isSimpleLocalName) {
      return { isValid: false, error: 'Only local router domain names (.local, .lan, .home) are permitted.' };
    }

    const portSuffix = port ? `:${port}` : '';
    return { isValid: true, baseUrl: `${protocol}//${cleanHostname}${portSuffix}` };
  }
}
