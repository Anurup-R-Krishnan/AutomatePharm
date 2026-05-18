/**
 * face_detection.js
 * Handles webcam capture, face descriptor extraction,
 * and communication with backend face routes.
 *
 * Depends on: face-api.js (loaded via CDN in HTML)
 * Models path: /static/models/
 */

const FaceDetection = (function () {
  'use strict';

  const MODEL_URL = '/static/models';
  let modelsLoaded = false;

  /* ── Load all 3 models ── */
  async function loadModels() {
    if (modelsLoaded) return;
    await Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
      faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
      faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
    ]);
    modelsLoaded = true;
    console.log('Face models loaded');
  }

  /* ── Start webcam stream into a <video> element ── */
  async function startCamera(videoEl) {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 320, height: 240, facingMode: 'user' }
    });
    videoEl.srcObject = stream;
    return new Promise((resolve) => {
      videoEl.onloadedmetadata = () => {
        videoEl.play();
        resolve(stream);
      };
    });
  }

  /* ── Stop webcam stream ── */
  function stopCamera(stream) {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
  }

  /* ── Get 128-dim descriptor from video frame ── */
  async function getDescriptor(videoEl) {
    const options = new faceapi.TinyFaceDetectorOptions({
      inputSize: 320,
      scoreThreshold: 0.5
    });

    const detection = await faceapi
      .detectSingleFace(videoEl, options)
      .withFaceLandmarks()
      .withFaceDescriptor();

    if (!detection) return null;
    return Array.from(detection.descriptor); // 128 floats
  }

  /* ── Register face for a customer ── */
  async function registerFace(videoEl, customerId) {
    const descriptor = await getDescriptor(videoEl);
    if (!descriptor) {
      return { status: 'error', message: 'No face detected. Try again.' };
    }

    const res = await fetch('/api/face/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ customer_id: customerId, descriptor })
    });
    return await res.json();
  }

  /* ── Identify face against all stored customers ── */
  async function identifyFace(videoEl) {
    const descriptor = await getDescriptor(videoEl);
    if (!descriptor) {
      return { status: 'error', message: 'No face detected. Try again.' };
    }

    const res = await fetch('/api/face/identify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ descriptor, threshold: 0.45 })
    });
    return await res.json();
  }

  /* ── Public API ── */
  return {
    loadModels,
    startCamera,
    stopCamera,
    getDescriptor,
    registerFace,
    identifyFace,
  };

})();
