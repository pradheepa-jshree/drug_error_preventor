"use client";


import { useState } from "react";

type OCRResult = {
  text: string;
  dosage: string;
  frequency: string;
  ocr_confidence: number;
};

export default function Home() {
  const [patientPhone, setPatientPhone] = useState("");
  const [prescriptionFile, setPrescriptionFile] = useState<File | null>(null);
  const [barcodeFile, setBarcodeFile] = useState<File | null>(null);

  const [prescriptionPreview, setPrescriptionPreview] = useState("");
  const [barcodePreview, setBarcodePreview] = useState("");

  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  type BarcodeResult = {
    gtin: string | null;
    drug_id: number | null;
    generic_name: string | null;
    brand_name: string | null;
    found: boolean;
  };

const [barcodeResult, setBarcodeResult] = useState<BarcodeResult | null>(null);
const handleBarcode = async () => {
  if (!barcodeFile) {
    alert("Please upload a barcode image first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", barcodeFile);

  try {
    const response = await fetch("http://localhost:8000/barcode", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("Barcode request failed");
    }

    const data = await response.json();
    setBarcodeResult(data);
  } catch (error) {
    console.error(error);
    alert("Unable to connect to the barcode server.");
  }
};
  const handleOCR = async () => {
    if (!prescriptionFile) {
      alert("Please upload a prescription image first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", prescriptionFile);

    try {
      const response = await fetch("http://localhost:8000/ocr", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("OCR request failed");
      }

      const data = await response.json();
      setOcrResult(data[0]);
    } catch (error) {
      console.error(error);
      alert("Unable to connect to the OCR server.");
    }
  };
  const handleConfirm = () => {
    alert("Prescription confirmed successfully!");
  };

  const handleCorrect = () => {
    alert("Correction option selected.");
  };

  const handleOverride = () => {
    alert("Override option selected.");
  };

  return (
    <main className="min-h-screen bg-slate-100 p-6">
      
      {/* Header */}
      <header className="mb-6 rounded-xl bg-blue-700 p-6 text-white shadow-lg">
        <h1 className="text-3xl font-bold">
          LASA Guardian
        </h1>
        <p className="mt-1 text-blue-100">
          Pharmacist Prescription Safety Dashboard
        </p>
      </header>

      {/* Patient Information */}
      <section className="mb-6 rounded-xl bg-white p-6 shadow">
        <h2 className="mb-4 text-xl font-bold text-slate-800">
          Patient Information
        </h2>

        <label className="mb-2 block font-medium text-slate-700">
          Patient Phone Number
        </label>

        <input
          type="text"
          placeholder="Enter patient phone number"
          value={patientPhone}
          onChange={(e) => setPatientPhone(e.target.value)}
          className="w-full rounded-lg border border-slate-300 p-3 outline-none focus:border-blue-500"
        />
      </section>

      {/* Upload Section */}
      <section className="mb-6 grid gap-6 md:grid-cols-2">

        {/* Prescription Upload */}
        <div className="rounded-xl bg-white p-6 shadow">
          <h2 className="mb-4 text-xl font-bold text-slate-800">
            Prescription Image
          </h2>

          <input
            type="file"
            accept="image/*"
            onChange={(e) => {
              const file = e.target.files?.[0] || null;
              setPrescriptionFile(file);

              if (file) {
                setPrescriptionPreview(URL.createObjectURL(file));
              }
            }}
            className="w-full rounded-lg border border-slate-300 p-3"
          />

          {prescriptionFile && (
            <p className="mt-3 text-sm text-green-600">
              ✓ {prescriptionFile.name} selected
            </p>
          )}

          <button
            onClick={handleOCR}
            className="mt-4 w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white hover:bg-blue-700"
          >
            Analyze Prescription
          </button>
          {prescriptionPreview && (
            <img
              src={prescriptionPreview}
              alt="Prescription preview"
              className="mt-4 max-h-64 w-full rounded-lg border object-contain"
            />
          )}
        </div>

        {/* Barcode Upload */}
        <div className="rounded-xl bg-white p-6 shadow">
          <h2 className="mb-4 text-xl font-bold text-slate-800">
            Barcode Image
          </h2>

          <input
            type="file"
            accept="image/*"
            onChange={(e) => {
              const file = e.target.files?.[0] || null;
              setBarcodeFile(file);

              if (file) {
                setBarcodePreview(URL.createObjectURL(file));
              }
            }}
            className="w-full rounded-lg border border-slate-300 p-3"
          />

          {barcodeFile && (
            <p className="mt-3 text-sm text-green-600">
              ✓ {barcodeFile.name} selected
            </p>
          )}
          <button
            onClick={handleBarcode}
            className="mt-4 w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white hover:bg-blue-700"
          >
            Analyze Barcode
          </button>
          {barcodePreview && (
            <img
              src={barcodePreview}
              alt="Barcode preview"
              className="mt-4 max-h-64 w-full rounded-lg border object-contain"
            />
          )}
        </div>
      </section>

      {/* OCR Results */}
      <section className="mb-6 rounded-xl bg-white p-6 shadow">
        <h2 className="mb-5 text-xl font-bold text-slate-800">
          OCR Results
        </h2>

        <div className="grid gap-4 md:grid-cols-4">

          <div className="rounded-lg bg-slate-100 p-4">
            <p className="text-sm text-slate-500">
              Medicine
            </p>
            <p className="mt-1 text-lg font-bold text-slate-800">
              {ocrResult?.text || "Waiting for OCR..."}
            </p>
          </div>

          <div className="rounded-lg bg-slate-100 p-4">
            <p className="text-sm text-slate-500">
              Dosage
            </p>
            <p className="mt-1 text-lg font-bold text-slate-800">
              {ocrResult?.dosage || "Waiting for OCR..."}
            </p>
          </div>

          <div className="rounded-lg bg-slate-100 p-4">
            <p className="text-sm text-slate-500">
              Frequency
            </p>
            <p className="mt-1 text-lg font-bold text-slate-800">
              {ocrResult?.frequency || "Waiting for OCR..."}
            </p>
          </div>

          <div className="rounded-lg bg-slate-100 p-4">
            <p className="text-sm text-slate-500">
              Confidence
            </p>
            <p className="mt-1 text-lg font-bold text-orange-600">
              {ocrResult
                ? `${(ocrResult.ocr_confidence * 100).toFixed(0)}%`
                : "Waiting for OCR..."}
            </p>
          </div>

        </div>
      </section>

      {/* Barcode Verification */}
      <section className="mb-6 rounded-xl bg-white p-6 shadow">
        <h2 className="mb-4 text-xl font-bold text-slate-800">
          Barcode Verification
        </h2>

        <div className="rounded-lg bg-slate-100 p-4">
          <p className="text-sm text-slate-500">
            Barcode Medicine
          </p>

          <p className="mt-1 text-lg font-bold text-slate-800">
            Amlopres
          </p>
        </div>

        {/* Mismatch Alert */}
        <div className="mt-4 rounded-lg border border-red-300 bg-red-50 p-4">
          <p className="font-bold text-red-700">
            ⚠️ Medicine Mismatch Detected
          </p>

          <p className="mt-1 text-red-600">
            OCR result: Aml0dipine
          </p>

          <p className="text-red-600">
            Barcode result: Amlopres
          </p>
        </div>
      </section>

      {/* Safety Warnings */}
      <section className="mb-6 rounded-xl bg-white p-6 shadow">
        <h2 className="mb-4 text-xl font-bold text-slate-800">
          Safety Warnings
        </h2>

        <div className="space-y-3">

          <div className="rounded-lg border border-red-300 bg-red-50 p-4">
            <p className="font-bold text-red-700">
              ⚠️ LASA Warning
            </p>
            <p className="text-red-600">
              Similar-looking or similar-sounding medicine detected.
            </p>
          </div>

          <div className="rounded-lg border border-orange-300 bg-orange-50 p-4">
            <p className="font-bold text-orange-700">
              ⚠️ Dosage Warning
            </p>
            <p className="text-orange-600">
              Please verify the prescribed dosage before dispensing.
            </p>
          </div>

          <div className="rounded-lg border border-yellow-300 bg-yellow-50 p-4">
            <p className="font-bold text-yellow-700">
              ⚠️ Interaction Warning
            </p>
            <p className="text-yellow-700">
              Check the patient's medication history for possible interactions.
            </p>
          </div>

        </div>
      </section>

      {/* Action Buttons */}
      <section className="mb-6 rounded-xl bg-white p-6 shadow">
        <h2 className="mb-4 text-xl font-bold text-slate-800">
          Pharmacist Action
        </h2>

        <div className="flex flex-wrap gap-4">

          <button
            onClick={handleConfirm}
            className="rounded-lg bg-green-600 px-6 py-3 font-bold text-white hover:bg-green-700"
          >
            ✓ Confirm
          </button>

          <button
            onClick={handleCorrect}
            className="rounded-lg bg-blue-600 px-6 py-3 font-bold text-white hover:bg-blue-700"
          >
            ✎ Correct
          </button>

          <button
            onClick={handleOverride}
            className="rounded-lg bg-red-600 px-6 py-3 font-bold text-white hover:bg-red-700"
          >
            ⚠ Override
          </button>

        </div>
      </section>

      {/* Footer */}
      <footer className="py-4 text-center text-sm text-slate-500">
        LASA Guardian • Prescription Safety System
      </footer>

    </main>
  );
}