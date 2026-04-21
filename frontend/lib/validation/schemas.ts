import { z } from "zod";

// US States and Territories
export const US_STATES_AND_TERRITORIES = [
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
  "DC", "AS", "GU", "MP", "PR", "VI"
] as const;

// Date of Birth validation
export const dateOfBirthSchema = z
  .string()
  .min(1, "Please enter a valid date of birth")
  .refine(
    (val) => {
      const date = new Date(val);
      if (isNaN(date.getTime())) return false;
      
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      // Cannot be in the future
      if (date > today) return false;
      
      // Cannot be more than 120 years ago
      const minDate = new Date();
      minDate.setFullYear(today.getFullYear() - 120);
      
      return date >= minDate;
    },
    { message: "Please enter a valid date of birth" }
  );

// Phone number validation (US format: (XXX) XXX-XXXX)
export const phoneSchema = z
  .string()
  .min(1, "Please enter a valid US phone number")
  .refine(
    (val) => {
      // Remove formatting for validation
      const digits = val.replace(/\D/g, "");
      
      // Must be 10 digits
      if (digits.length !== 10) return false;
      
      // Area code first digit must be 2-9
      const areaCode = digits[0];
      if (areaCode < "2" || areaCode > "9") return false;
      
      // Exchange code first digit must be 2-9
      const exchangeCode = digits[3];
      if (exchangeCode < "2" || exchangeCode > "9") return false;
      
      return true;
    },
    { message: "Please enter a valid US phone number" }
  );

// Email validation
export const emailSchema = z
  .string()
  .min(1, "Please enter a valid email address")
  .email("Please enter a valid email address")
  .refine(
    (val) => {
      // Must contain @ symbol
      if (!val.includes("@")) return false;
      
      // Must have valid domain format (xxx@xxx.xxx)
      const parts = val.split("@");
      if (parts.length !== 2) return false;
      
      const [local, domain] = parts;
      if (!local || !domain) return false;
      
      // Domain must contain at least one dot
      if (!domain.includes(".")) return false;
      
      // No brackets or special characters except . - _ + in local part
      const localRegex = /^[a-zA-Z0-9._+-]+$/;
      if (!localRegex.test(local)) return false;
      
      // Domain must be valid
      const domainRegex = /^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      if (!domainRegex.test(domain)) return false;
      
      return true;
    },
    { message: "Please enter a valid email address" }
  );

// Name validation
export const nameSchema = z
  .string()
  .min(2, "Please enter a valid name")
  .refine(
    (val) => {
      // Only letters, spaces, hyphens, apostrophes
      const nameRegex = /^[a-zA-Z\s'-]+$/;
      return nameRegex.test(val);
    },
    { message: "Please enter a valid name" }
  );

// State validation
export const stateSchema = z
  .string()
  .min(2, "Please select a valid state")
  .refine(
    (val) => US_STATES_AND_TERRITORIES.includes(val as any),
    { message: "Please select a valid state" }
  );

// ZIP code validation (US format)
export const zipCodeSchema = z
  .string()
  .min(5, "Please enter a valid ZIP code")
  .refine(
    (val) => {
      // 5 digits or 5+4 format
      const zipRegex = /^\d{5}(-\d{4})?$/;
      return zipRegex.test(val);
    },
    { message: "Please enter a valid ZIP code" }
  );

// Patient intake form schema
export const patientIntakeSchema = z.object({
  firstName: nameSchema,
  lastName: nameSchema,
  dateOfBirth: dateOfBirthSchema,
  email: emailSchema,
  phone: phoneSchema,
  address: z.string().min(1, "Please enter a valid address").optional(),
  city: z.string().min(1, "Please enter a valid city").optional(),
  state: stateSchema.optional(),
  zipCode: zipCodeSchema.optional(),
});

export type PatientIntakeFormData = z.infer<typeof patientIntakeSchema>;

