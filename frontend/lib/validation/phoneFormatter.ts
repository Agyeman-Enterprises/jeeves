/**
 * Formats a phone number as user types: (XXX) XXX-XXXX
 */
export function formatPhoneNumber(value: string): string {
  // Remove all non-digits
  const digits = value.replace(/\D/g, "");
  
  // Limit to 10 digits
  const limited = digits.slice(0, 10);
  
  // Format based on length
  if (limited.length === 0) return "";
  if (limited.length <= 3) return `(${limited}`;
  if (limited.length <= 6) return `(${limited.slice(0, 3)}) ${limited.slice(3)}`;
  return `(${limited.slice(0, 3)}) ${limited.slice(3, 6)}-${limited.slice(6)}`;
}

/**
 * Validates if a phone number is in valid US format
 */
export function isValidPhoneNumber(value: string): boolean {
  const digits = value.replace(/\D/g, "");
  
  if (digits.length !== 10) return false;
  
  // Area code first digit must be 2-9
  const areaCode = digits[0];
  if (areaCode < "2" || areaCode > "9") return false;
  
  // Exchange code first digit must be 2-9
  const exchangeCode = digits[3];
  if (exchangeCode < "2" || exchangeCode > "9") return false;
  
  return true;
}

