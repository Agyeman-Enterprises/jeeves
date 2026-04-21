"use client";

import { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  touched?: boolean;
  showError?: boolean;
  as?: "input" | "textarea";
  textareaProps?: TextareaHTMLAttributes<HTMLTextAreaElement>;
}

export function FormField({
  label,
  error,
  touched,
  showError = true,
  className = "",
  as = "input",
  textareaProps,
  ...inputProps
}: FormFieldProps) {
  const hasError = touched && error;
  const inputClassName = `
    w-full px-3 py-2 border rounded-md
    focus:outline-none focus:ring-2 focus:ring-blue-500
    ${hasError ? "border-red-500 focus:ring-red-500" : "border-gray-300"}
    ${inputProps.disabled ? "bg-gray-100 cursor-not-allowed" : "bg-white"}
    ${className}
  `.trim();

  return (
    <div className="mb-4">
      <label htmlFor={inputProps.id} className="block text-sm font-medium text-gray-700 mb-1">
        {label}
        {inputProps.required && <span className="text-red-500 ml-1">*</span>}
      </label>
      
      {as === "textarea" ? (
        <textarea
          {...textareaProps}
          className={inputClassName}
          aria-invalid={hasError ? "true" : "false"}
          aria-describedby={hasError ? `${inputProps.id}-error` : undefined}
        />
      ) : (
        <input
          {...inputProps}
          className={inputClassName}
          aria-invalid={hasError ? "true" : "false"}
          aria-describedby={hasError ? `${inputProps.id}-error` : undefined}
        />
      )}
      
      {showError && hasError && (
        <p id={`${inputProps.id}-error`} className="mt-1 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

