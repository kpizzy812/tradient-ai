import useSWR from 'swr';
import { fetchProfile } from '@/shared/api';

export const useProfile = () => {
  const { data, error, isLoading, mutate } = useSWR(
    'profile',
    fetchProfile,
    {
      revalidateOnFocus: false,
    }
  );

  return {
    // Добавили поле profile, которое хранит весь объект данных
    profile: data,
    userId: data?.user_id,
    isLoading,
    error,
    mutate,
  };
};
