"use client";

import { useState } from "react";
import { useFormValidation } from "@/lib/validation/useFormValidation";
import { patientIntakeSchema, type PatientIntakeFormData } from "@/lib/validation/schemas";
import { formatPhoneNumber } from "@/lib/validation/phoneFormatter";
import { FormField } from "./FormField";
import { US_STATES_AND_TERRITORIES } from "@/lib/validation/schemas";

interface PatientIntakeFormProps {
  onSubmit: (data: PatientIntakeFormData) => void | Promise<void>;
  initialData?: Partial<PatientIntakeFormData>;
}

export function PatientIntakeForm({ onSubmit, initialData }: PatientIntakeFormProps) {
  const [formData, setFormData] = useState<Partial<PatientIntakeFormData>>({
    firstName: "",
    lastName: "",
    dateOfBirth: "",
    email: "",
    phone: "",
    address: "",
    city: "",
    state: "",
    zipCode: "",
    ...initialData,
  });

  const {
    errors,
    touched,
    isSubmitting,
    handleBlur,
    handleChange,
    handleSubmit,
    getFieldError,
    isFieldValid,
    isFormValid,
  } = useFormValidation({
    schema: patientIntakeSchema,
    onSubmit,
    validateOnBlur: true,
    validateOnChange: true,
  });

  const onFieldChange = (name: string, value: string) => {
    // Special handling for phone number formatting
    if (name === "phone") {
      value = formatPhoneNumber(value);
    }
    
    setFormData((prev) => ({ ...prev, [name]: value }));
    handleChange(name, value);
  };

  const onFieldBlur = (name: string) => {
    handleBlur(name, formData[name as keyof PatientIntakeFormData]);
  };

  const onSubmitForm = (e: React.FormEvent) => {
    e.preventDefault();
    handleSubmit(formData as PatientIntakeFormData);
  };

  return (
    <form onSubmit={onSubmitForm} className="max-w-2xl mx-auto p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <FormField
          id="firstName"
          label="First Name"
          type="text"
          value={formData.firstName || ""}
          onChange={(e) => onFieldChange("firstName", e.target.value)}
          onBlur={() => onFieldBlur("firstName")}
          error={getFieldError("firstName")}
          touched={touched.firstName}
          required
        />

        <FormField
          id="lastName"
          label="Last Name"
          type="text"
          value={formData.lastName || ""}
          onChange={(e) => onFieldChange("lastName", e.target.value)}
          onBlur={() => onFieldBlur("lastName")}
          error={getFieldError("lastName")}
          touched={touched.lastName}
          required
        />
      </div>

      <FormField
        id="dateOfBirth"
        label="Date of Birth"
        type="date"
        value={formData.dateOfBirth || ""}
        onChange={(e) => onFieldChange("dateOfBirth", e.target.value)}
        onBlur={() => onFieldBlur("dateOfBirth")}
        error={getFieldError("dateOfBirth")}
        touched={touched.dateOfBirth}
        required
      />

      <FormField
        id="email"
        label="Email"
        type="email"
        value={formData.email || ""}
        onChange={(e) => onFieldChange("email", e.target.value)}
        onBlur={() => onFieldBlur("email")}
        error={getFieldError("email")}
        touched={touched.email}
        required
      />

      <FormField
        id="phone"
        label="Phone Number"
        type="tel"
        placeholder="(XXX) XXX-XXXX"
        value={formData.phone || ""}
        onChange={(e) => onFieldChange("phone", e.target.value)}
        onBlur={() => onFieldBlur("phone")}
        error={getFieldError("phone")}
        touched={touched.phone}
        required
        maxLength={14} // (XXX) XXX-XXXX
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2">
          <FormField
            id="address"
            label="Address"
            type="text"
            value={formData.address || ""}
            onChange={(e) => onFieldChange("address", e.target.value)}
            onBlur={() => onFieldBlur("address")}
            error={getFieldError("address")}
            touched={touched.address}
          />
        </div>

        <FormField
          id="city"
          label="City"
          type="text"
          value={formData.city || ""}
          onChange={(e) => onFieldChange("city", e.target.value)}
          onBlur={() => onFieldBlur("city")}
          error={getFieldError("city")}
          touched={touched.city}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="state" className="block text-sm font-medium text-gray-700 mb-1">
            State
          </label>
          <select
            id="state"
            value={formData.state || ""}
            onChange={(e) => onFieldChange("state", e.target.value)}
            onBlur={() => onFieldBlur("state")}
            className={`
              w-full px-3 py-2 border rounded-md
              focus:outline-none focus:ring-2 focus:ring-blue-500
              ${touched.state && errors.state ? "border-red-500 focus:ring-red-500" : "border-gray-300"}
            `}
            aria-invalid={touched.state && errors.state ? "true" : "false"}
            aria-describedby={touched.state && errors.state ? "state-error" : undefined}
          >
            <option value="">Select a state</option>
            {US_STATES_AND_TERRITORIES.map((state) => (
              <option key={state} value={state}>
                {state}
              </option>
            ))}
          </select>
          {touched.state && errors.state && (
            <p id="state-error" className="mt-1 text-sm text-red-600" role="alert">
              {errors.state}
            </p>
          )}
        </div>

        <FormField
          id="zipCode"
          label="ZIP Code"
          type="text"
          placeholder="12345"
          value={formData.zipCode || ""}
          onChange={(e) => onFieldChange("zipCode", e.target.value)}
          onBlur={() => onFieldBlur("zipCode")}
          error={getFieldError("zipCode")}
          touched={touched.zipCode}
        />
      </div>

      <div className="mt-6">
        <button
          type="submit"
          disabled={!isFormValid() || isSubmitting}
          className={`
            w-full px-4 py-2 rounded-md font-medium
            ${!isFormValid() || isSubmitting
              ? "bg-gray-300 text-gray-500 cursor-not-allowed"
              : "bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            }
            transition-colors
          `}
        >
          {isSubmitting ? "Submitting..." : "Continue"}
        </button>
      </div>
    </form>
  );
}

