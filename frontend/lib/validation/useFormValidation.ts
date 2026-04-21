"use client";

import { useState, useCallback, useEffect } from "react";
import { z } from "zod";

export interface ValidationErrors {
  [key: string]: string | undefined;
}

export interface UseFormValidationOptions<T> {
  schema: z.ZodSchema<T>;
  onSubmit: (data: T) => void | Promise<void>;
  validateOnBlur?: boolean;
  validateOnChange?: boolean;
}

export function useFormValidation<T extends Record<string, any>>({
  schema,
  onSubmit,
  validateOnBlur = true,
  validateOnChange = false,
}: UseFormValidationOptions<T>) {
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateField = useCallback(
    (name: string, value: any): string | undefined => {
      try {
        // Extract field schema if possible
        const fieldSchema = (schema as any).shape?.[name];
        if (fieldSchema) {
          fieldSchema.parse(value);
        }
        return undefined;
      } catch (error) {
        if (error instanceof z.ZodError) {
          return error.issues[0]?.message || "Invalid value";
        }
        return "Invalid value";
      }
    },
    [schema]
  );

  const validateForm = useCallback(
    (data: T): boolean => {
      try {
        schema.parse(data);
        setErrors({});
        return true;
      } catch (error) {
        if (error instanceof z.ZodError) {
          const newErrors: ValidationErrors = {};
          error.issues.forEach((issue) => {
            const path = issue.path.join(".");
            newErrors[path] = issue.message;
          });
          setErrors(newErrors);
        }
        return false;
      }
    },
    [schema]
  );

  const handleBlur = useCallback(
    (name: string, value: any) => {
      if (validateOnBlur) {
        setTouched((prev) => ({ ...prev, [name]: true }));
        const error = validateField(name, value);
        setErrors((prev) => ({ ...prev, [name]: error }));
      }
    },
    [validateOnBlur, validateField]
  );

  const handleChange = useCallback(
    (name: string, value: any) => {
      if (validateOnChange && touched[name]) {
        const error = validateField(name, value);
        setErrors((prev) => ({ ...prev, [name]: error }));
      }
    },
    [validateOnChange, touched, validateField]
  );

  const handleSubmit = useCallback(
    async (data: T) => {
      // Mark all fields as touched
      const allTouched: Record<string, boolean> = {};
      Object.keys(data).forEach((key) => {
        allTouched[key] = true;
      });
      setTouched(allTouched);

      // Validate entire form
      if (!validateForm(data)) {
        return;
      }

      setIsSubmitting(true);
      try {
        await onSubmit(data);
      } finally {
        setIsSubmitting(false);
      }
    },
    [validateForm, onSubmit]
  );

  const getFieldError = useCallback(
    (name: string): string | undefined => {
      return touched[name] ? errors[name] : undefined;
    },
    [errors, touched]
  );

  const isFieldValid = useCallback(
    (name: string): boolean => {
      return !touched[name] || !errors[name];
    },
    [errors, touched]
  );

  const isFormValid = useCallback((): boolean => {
    return Object.keys(errors).length === 0 || Object.values(errors).every((err) => !err);
  }, [errors]);

  return {
    errors,
    touched,
    isSubmitting,
    handleBlur,
    handleChange,
    handleSubmit,
    getFieldError,
    isFieldValid,
    isFormValid,
    validateForm,
  };
}

