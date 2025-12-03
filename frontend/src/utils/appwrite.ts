import { Client, Account, Databases, Storage } from 'appwrite';

export const PROJECT_ID = import.meta.env.VITE_APPWRITE_PROJECT_ID || '692598380015d5816b7e';
export const API_ENDPOINT = import.meta.env.VITE_APPWRITE_ENDPOINT || 'https://fra.cloud.appwrite.io/v1';
export const DATABASE_ID = import.meta.env.VITE_APPWRITE_DATABASE_ID || 'job-market-db';
export const COLLECTION_ID_JOBS = 'jobs';
export const COLLECTION_ID_APPLICATIONS = 'applications';
export const COLLECTION_ID_PROFILES = 'profiles';
export const BUCKET_ID_CVS = 'cv-bucket';

const client = new Client();

client
    .setEndpoint(API_ENDPOINT)
    .setProject(PROJECT_ID);

export const account = new Account(client);
export const databases = new Databases(client);
export const storage = new Storage(client);

export default client;
