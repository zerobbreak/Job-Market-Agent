import { Client, Account, Databases, Storage } from 'appwrite';

export const PROJECT_ID = import.meta.env.VITE_APPWRITE_PROJECT_ID;
export const API_ENDPOINT = import.meta.env.VITE_APPWRITE_ENDPOINT;
export const DATABASE_ID = import.meta.env.VITE_APPWRITE_DATABASE_ID;
export const COLLECTION_ID_JOBS = 'jobs';
export const COLLECTION_ID_APPLICATIONS = 'applications';
export const COLLECTION_ID_PROFILES = 'profiles';
export const BUCKET_ID_CVS = 'cv-bucket';

const client = new Client();

const hasConfig = Boolean(API_ENDPOINT) && Boolean(PROJECT_ID);
if (hasConfig) {
  client.setEndpoint(API_ENDPOINT as string).setProject(PROJECT_ID as string);
}

export const account = new Account(client);
export const databases = new Databases(client);
export const storage = new Storage(client);

export default client;
