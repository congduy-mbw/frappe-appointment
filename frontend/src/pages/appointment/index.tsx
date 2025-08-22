/**
 * External dependencies
 */
import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useFrappeGetCall } from "frappe-react-sdk";

/**
 * Internal dependencies
 */
import { Avatar, AvatarFallback, AvatarImage } from "@/components/avatar";
import { MeetingCardSkeleton, ProfileSkeleton } from "./components/skeletons";
import MeetingCard from "./components/meetingCard";
import Booking from "./components/booking";
import SocialProfiles from "./components/socialProfiles";
import { useAppContext } from "@/context/app";
import { Skeleton } from "@/components/skeleton";
import { getLocalTimezone } from "@/lib/utils";
import PoweredBy from "@/components/powered-by";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/tooltip";
import Typography from "@/components/typography";
import MetaTags from "@/components/meta-tags";
import { Info } from "lucide-react";

const Appointment = () => {
  const { meetId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const type = searchParams.get("type");
  const email = searchParams.get("email");
  const fullname = searchParams.get("fullname");
  const task_id = searchParams.get("taskId") || searchParams.get("task_id") || searchParams.get("taskid");
  const type_app = searchParams.get("type_app") || searchParams.get("typeApp");

  const {
    setMeetingId,
    setUserInfo,
    userInfo,
    setDuration,
    setTimeZone,
    meetingDurationCards,
    setMeetingDurationCards,
  } = useAppContext();

  // Lưu email và fullname vào state local khi chúng có trong URL
  const [visitorEmail, setVisitorEmail] = useState<string | null>(null);
  const [visitorName, setVisitorName] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [typeApp, setTypeApp] = useState<string | null>(null);

  // Lưu thông tin khách từ URL vào state
  useEffect(() => {
    if (email) {
      setVisitorEmail(email);
    }
    if (fullname) {
      setVisitorName(fullname);
    }
    if(task_id){
      setTaskId(task_id);
    }
    if(type_app){
      setTypeApp(type_app);
    }
  }, [email, fullname, task_id, type_app]);

  // Sử dụng thông tin khách trong quá trình đặt lịch hẹn
  useEffect(() => {
    // Chỉ thực hiện khi đã chọn type (đã chuyển sang màn hình đặt lịch)
    if (type && visitorEmail && visitorName) {
      // Có thể truyền thông tin này vào component Booking hoặc sử dụng trong API calls sau này
    }
  }, [type, visitorEmail, visitorName]);

  const updateTypeQuery = (type: string) => {
    setSearchParams({ type });
  };

  const navigate = useNavigate();

  const { data, isLoading, error } = useFrappeGetCall(
    "frappe_appointment.api.personal_meet.get_meeting_windows",
    {
      slug: meetId,
    },
    undefined,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      errorRetryCount: 3,
    }
  );

  useEffect(() => {
    if (meetId) {
      setMeetingId(meetId);
    }
    setTimeZone(getLocalTimezone());
  }, []);

  useEffect(() => {
    if (data) {
      console.log(data)
      setUserInfo({
        name: data?.message?.full_name,
        designation: data?.message?.position,
        organizationName: data?.message?.company,
        userImage: data?.message?.profile_pic,
        socialProfiles: [],
        meetingProvider: data?.message?.meeting_provider,
        banner_image: data?.message?.banner_image,
      });
      setMeetingDurationCards(data?.message?.durations);
      
      // Nếu typeApp là mbw_mia hoặc mbw_avi thì tự động chọn meeting card đầu tiên và vào booking
      // Chỉ thực hiện khi chưa có type để tránh vòng lặp vô tận
      if ((typeApp === "mbw_mia" || typeApp === "mbw_avi") && 
          !type && 
          data?.message?.durations && 
          data?.message?.durations.length > 0) {
        const firstCard = data.message.durations[0];
        setDuration(firstCard.duration / 60);
        updateTypeQuery(firstCard.id);
      }
    }
    if (error) {
      navigate("/");
    }
  }, [data, error, typeApp, type]);

  return (
    <>
      <MetaTags
        title={userInfo.name ? `${userInfo.name} | Appointment` : "Appointment"}
        description={`Book appointment with ${userInfo.name}`}
      />
      {!type || !typeApp || isLoading ? (
        <div className="w-full h-full max-md:h-fit flex justify-center">
          <div className="container max-w-[74rem] mx-auto md:p-4 md:py-8 lg:py-16 grid md:gap-12">
            <div className="grid lg:grid-cols-[360px,1fr] md:gap-8 max-md:gap-10  items-start relative rounded-lg">
              {/* Profile Section */}
              {isLoading ? (
                <ProfileSkeleton />
              ) : (
                <div className="w-full flex flex-col gap-4 p-4 md:p-6 max-lg:md:pt-10 md:px-4 justify-center items-center bg-gradient-to-b from-blue-100 to-transparent dark:bg-gradient-to-b dark:from-zinc-800 md:rounded-2xl">
                  <Avatar className="md:h-32 md:w-32 h-24 w-24 object-cover mb-4 md:mb-0 hover:outline outline-blue-300 dark:outline-blue-400/80 transition-all duration-100">
                    <AvatarImage
                      src={userInfo.userImage}
                      alt="Profile picture"
                      className="bg-blue-50 dark:bg-zinc-800"
                    />
                    <AvatarFallback className="text-4xl">
                      {userInfo?.name?.toString()[0]?.toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="w-full flex flex-col gap-1">
                    <Typography variant="h2" className="text-3xl font-semibold">
                      <Tooltip>
                        <TooltipTrigger className="truncate w-full">
                          {userInfo.name}
                        </TooltipTrigger>
                        <TooltipContent>{userInfo.name}</TooltipContent>
                      </Tooltip>
                    </Typography>
                    {userInfo.designation && userInfo.organizationName && (
                      <Tooltip>
                        <TooltipTrigger className="w-full">
                          <Typography className="text-base text-muted-foreground">
                            {userInfo.designation} at{" "}
                            {userInfo.organizationName}
                          </Typography>
                        </TooltipTrigger>
                        <TooltipContent>
                          {userInfo.designation} at {userInfo.organizationName}
                        </TooltipContent>
                      </Tooltip>
                    )}
                  </div>
                  <SocialProfiles profiles={userInfo.socialProfiles} />
                </div>
              )}

              {/* Meeting Options */}
              <div className="space-y-6 p-4 md:p-6 md:pt-0">
                {isLoading ? (
                  <>
                    <Skeleton className="h-6 md:w-56" />
                    <Skeleton className="h-4 md:w-72" />
                  </>
                ) : (
                  <div>
                    <h2 className="text-xl font-semibold mb-2">
                      Select Meeting Duration
                    </h2>
                    <p className="text-muted-foreground">
                      You will receive a calendar invite with meeting link.
                    </p>
                  </div>
                )}
                {/* meeting cards */}
                <div className="grid sm:grid-cols-2 gap-4 h-full lg:pb-5 overflow-y-auto py-3">
                  {isLoading ? (
                    <>
                      <MeetingCardSkeleton />
                      <MeetingCardSkeleton />
                      <MeetingCardSkeleton />
                    </>
                  ) : (
                    meetingDurationCards.map((card) => (
                      <MeetingCard
                        key={card.id}
                        title={card.label}
                        duration={card.duration / 60}
                        onClick={() => {
                          setDuration(card.duration / 60);
                          updateTypeQuery(card.id);
                        }}
                      />
                    ))
                  )}
                </div>
                <div className="mt-4 p-3 md:hidden bg-gray-50 dark:bg-card rounded-2xl border border-gray-200 dark:border-gray-600 text-sm text-gray-600 dark:text-gray-400">
                  <div className="flex items-center gap-3">
                    <Info className="text-amber-500 size-10" />
                    <p>
                      All times are in your local timezone. Meetings can be
                      rescheduled if needed.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <Booking type={type || ""} banner={userInfo.banner_image} visitorEmail={visitorEmail} visitorName={visitorName} taskId={taskId} typeApp={typeApp} />
      )}
      <PoweredBy />
    </>
  );
};

export default Appointment;
