import type { Offer } from '../types';

const DELIMITER = '|';

/** Parse pipe-delimited CSV text (RFC4180-style quoting) into rows of raw string cells. */
export function parseDelimitedCsv(text: string, delimiter: string = DELIMITER): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];

    if (inQuotes) {
      if (char === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += char;
      }
      continue;
    }

    if (char === '"') {
      inQuotes = true;
    } else if (char === delimiter) {
      row.push(field);
      field = '';
    } else if (char === '\r') {
      // ignore, \n (or the final char) ends the row
    } else if (char === '\n') {
      row.push(field);
      rows.push(row);
      row = [];
      field = '';
    } else {
      field += char;
    }
  }

  if (field.length > 0 || row.length > 0) {
    row.push(field);
    rows.push(row);
  }

  return rows.filter((r) => r.length > 1 || r[0] !== '');
}

const HEADER_TO_FIELD: Record<string, keyof Offer> = {
  url: 'url',
  code: 'code',
  confidence: 'confidence',
  source: 'source',
  price: 'price',
  location: 'location',
  store_name: 'storeName',
  address_line1: 'addressLine1',
  address_line2: 'addressLine2',
  city: 'city',
  state: 'state',
  expires: 'expires',
  error: 'error',
};

/** Fetch and parse couponfinder's results.csv (served from the files/ folder) into Offer rows. */
export async function loadOffers(csvUrl: string = '/results.csv'): Promise<Offer[]> {
  const response = await fetch(csvUrl);
  if (!response.ok) {
    throw new Error(`Failed to load ${csvUrl}: ${response.status} ${response.statusText}`);
  }
  const text = await response.text();
  const rows = parseDelimitedCsv(text);
  if (rows.length === 0) {
    return [];
  }

  const [header, ...dataRows] = rows;
  const fieldOrder = header.map((h) => HEADER_TO_FIELD[h.trim()]);

  return dataRows.map((cells) => {
    const offer = {} as Offer;
    fieldOrder.forEach((field, index) => {
      if (field) {
        offer[field] = (cells[index] ?? '').trim();
      }
    });
    return offer;
  });
}
