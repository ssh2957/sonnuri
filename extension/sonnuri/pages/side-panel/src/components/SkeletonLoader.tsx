import React from 'react';
import { Skeleton } from '../../../../packages/ui/lib/components/ui';



const SkeletonLoader: React.FC = () => {
    return (
        <div className="flex flex-col items-center justify-center">
            <Skeleton className="h-48 w-full rounded-md flex flex-col items-center justify-center">
                <div className="flex justify-center mt-4">
                    <div className="w-8 h-8 border-4 border-black border-t-transparent rounded-full animate-spin"></div>
                </div>

            </Skeleton>
        </div>
    );
}

export default SkeletonLoader