import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyCIP_dN7K9whIe5lS39DsWsN7H0F1TIXGI",
  authDomain: "aegis-b25aa.firebaseapp.com",
  projectId: "aegis-b25aa",
  storageBucket: "aegis-b25aa.firebasestorage.app",
  messagingSenderId: "500292200561",
  appId: "1:500292200561:web:7c7983bc43b4dc721453d0",
  measurementId: "G-V4G6B20HWC"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
