const EMAIL_SHAPE =
  /^[a-z0-9](?:[a-z0-9._%+-]{0,62}[a-z0-9])?@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/;
const TLD_PATTERN = /^[a-z]{2,24}$/;
const LABEL_PATTERN = /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/;
const RESERVED_DOMAINS = new Set([
  'example.com',
  'example.net',
  'example.org',
  'example.edu',
  'invalid',
  'localhost',
  'local',
  'test',
]);
const PLACEHOLDER_LOCAL_PARTS = new Set([
  'abc',
  'asdf',
  'email',
  'fake',
  'foo',
  'test',
  'testing',
  'username',
]);

export const EMAIL_ERROR = 'Enter a valid email address, such as name@gmail.com.';

export function normalizeEmail(value: string): string {
  return value.trim().toLowerCase();
}

export function isValidEmail(value: string): boolean {
  const cleaned = normalizeEmail(value);
  if (!cleaned || cleaned.length > 254 || cleaned.includes('..') || !EMAIL_SHAPE.test(cleaned)) {
    return false;
  }

  const at = cleaned.indexOf('@');
  const local = cleaned.slice(0, at);
  const domain = cleaned.slice(at + 1);
  const labels = domain.split('.');
  if (!local || local.length > 64 || local.startsWith('.') || local.endsWith('.') || labels.length < 2) {
    return false;
  }
  if (labels.some((label) => !LABEL_PATTERN.test(label))) {
    return false;
  }
  const tld = labels[labels.length - 1];
  const sld = labels[labels.length - 2];
  if (!TLD_PATTERN.test(tld) || tld === sld || RESERVED_DOMAINS.has(domain) || RESERVED_DOMAINS.has(tld)) {
    return false;
  }
  return !PLACEHOLDER_LOCAL_PARTS.has(local);
}
